"""
minio_rest.py
=============
MinIO / S3 access via the REST API using pure `requests` + AWS SigV4 signing.
No s3fs, no boto3 (company policy: s3fs not permitted).

Usage:
    from minio_rest import MinioREST
    mc = MinioREST(endpoint="http://192.168.139.2:9000",
                   access_key="admin", secret_key="...", bucket="data-catalog-bucket")
    mc.put_bytes("path/to/obj", b"data")
    mc.put_parquet_table("path/to/obj.parquet", pyarrow_table)   # if pyarrow available
    data = mc.get_bytes("path/to/obj")
    mc.delete("path/to/obj")                 # single-object DELETE (no Content-MD5 needed)
    keys = mc.list("prefix/")                # recursive list of object keys (>0 bytes default)
    mc.exists("path/to/obj")                 # bool
    mc.delete_prefix("prefix/")              # delete every object under prefix, one at a time

Notes:
    * Keys are relative to the bucket (do NOT include the bucket in the key).
    * list() returns keys WITHOUT the bucket prefix.
    * Paths may be given as s3a://bucket/key or bucket/key or key — normalized internally.
"""
import hashlib
import hmac
import datetime
import xml.etree.ElementTree as ET
from urllib.parse import quote
import requests
import io


class MinioREST:
    def __init__(self, endpoint, access_key, secret_key, bucket, region="us-east-1"):
        self.endpoint = endpoint.rstrip("/")
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.region = region
        self.host = self.endpoint.split("://", 1)[1]

    # ---- key normalization ----
    def _key(self, path):
        """Normalize a path to a bucket-relative key.
        Accepts s3a://bucket/key, s3://bucket/key, bucket/key, or key."""
        p = path
        for scheme in ("s3a://", "s3://"):
            if p.startswith(scheme):
                p = p[len(scheme):]
                break
        if p.startswith(self.bucket + "/"):
            p = p[len(self.bucket) + 1:]
        return p.lstrip("/")

    # ---- SigV4 ----
    def _sign(self, key, msg):
        return hmac.new(key, msg.encode(), hashlib.sha256).digest()

    def _signing_key(self, datestamp):
        k = self._sign(("AWS4" + self.secret_key).encode(), datestamp)
        k = self._sign(k, self.region)
        k = self._sign(k, "s3")
        return self._sign(k, "aws4_request")

    def _request(self, method, key, query="", body=b""):
        """Signed S3 REST request. key is bucket-relative. Returns requests.Response."""
        canonical_uri = "/" + self.bucket + "/" + quote(key, safe="/")
        now = datetime.datetime.now(datetime.timezone.utc)
        amzdate = now.strftime("%Y%m%dT%H%M%SZ")
        datestamp = now.strftime("%Y%m%d")
        payload_hash = hashlib.sha256(body).hexdigest()

        canonical_querystring = query  # already canonical or empty
        canonical_headers = (f"host:{self.host}\n"
                             f"x-amz-content-sha256:{payload_hash}\n"
                             f"x-amz-date:{amzdate}\n")
        signed_headers = "host;x-amz-content-sha256;x-amz-date"
        canonical_request = (f"{method}\n{canonical_uri}\n{canonical_querystring}\n"
                             f"{canonical_headers}\n{signed_headers}\n{payload_hash}")

        algorithm = "AWS4-HMAC-SHA256"
        cred_scope = f"{datestamp}/{self.region}/s3/aws4_request"
        string_to_sign = (f"{algorithm}\n{amzdate}\n{cred_scope}\n"
                          f"{hashlib.sha256(canonical_request.encode()).hexdigest()}")
        signature = hmac.new(self._signing_key(datestamp),
                             string_to_sign.encode(), hashlib.sha256).hexdigest()
        auth = (f"{algorithm} Credential={self.access_key}/{cred_scope}, "
                f"SignedHeaders={signed_headers}, Signature={signature}")
        headers = {"Authorization": auth, "x-amz-date": amzdate,
                   "x-amz-content-sha256": payload_hash}
        url = f"{self.endpoint}{canonical_uri}"
        if query:
            url += "?" + query
        return requests.request(method, url, headers=headers, data=body)

    # ---- object operations ----
    def put_bytes(self, path, data: bytes):
        key = self._key(path)
        r = self._request("PUT", key, body=data)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"PUT {key} failed [{r.status_code}]: {r.text[:200]}")
        return r.status_code

    def get_bytes(self, path) -> bytes:
        key = self._key(path)
        r = self._request("GET", key)
        if r.status_code == 200:
            return r.content
        raise FileNotFoundError(f"GET {key} [{r.status_code}]")

    def delete(self, path):
        key = self._key(path)
        r = self._request("DELETE", key)
        # S3 DELETE is idempotent → 204 even if absent
        if r.status_code not in (200, 204):
            raise RuntimeError(f"DELETE {key} failed [{r.status_code}]: {r.text[:200]}")
        return r.status_code

    def exists(self, path) -> bool:
        key = self._key(path)
        r = self._request("HEAD", key)
        return r.status_code == 200

    def size(self, path) -> int:
        key = self._key(path)
        r = self._request("HEAD", key)
        if r.status_code == 200:
            return int(r.headers.get("Content-Length", 0))
        return -1

    def list(self, prefix="", min_size=1):
        """Recursive list of object keys (bucket-relative) under prefix.
        min_size: filter out objects smaller than this (default 1 → skips 0-byte
        directory markers). Set min_size=0 to include everything.
        Handles pagination via continuation tokens."""
        pfx = self._key(prefix) if prefix else ""
        keys = []
        token = None
        while True:
            # ListObjectsV2: list-type=2, prefix, optional continuation-token
            qparts = ["list-type=2"]
            if pfx:
                qparts.append("prefix=" + quote(pfx, safe=""))
            if token:
                qparts.append("continuation-token=" + quote(token, safe=""))
            query = "&".join(sorted(qparts))
            # signed GET on the BUCKET (key="")
            r = self._request_bucket("GET", query)
            if r.status_code != 200:
                if r.status_code == 404:
                    break
                raise RuntimeError(f"LIST failed [{r.status_code}]: {r.text[:200]}")
            ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
            root = ET.fromstring(r.text)
            for cont in root.findall("s3:Contents", ns):
                k = cont.find("s3:Key", ns).text
                sz = int(cont.find("s3:Size", ns).text)
                if sz >= min_size:
                    keys.append(k)
            truncated = root.find("s3:IsTruncated", ns)
            if truncated is not None and truncated.text == "true":
                nt = root.find("s3:NextContinuationToken", ns)
                token = nt.text if nt is not None else None
                if not token:
                    break
            else:
                break
        return keys

    def _request_bucket(self, method, query=""):
        """Signed request against the bucket root (for listing)."""
        canonical_uri = "/" + self.bucket + "/"
        now = datetime.datetime.now(datetime.timezone.utc)
        amzdate = now.strftime("%Y%m%dT%H%M%SZ")
        datestamp = now.strftime("%Y%m%d")
        payload_hash = hashlib.sha256(b"").hexdigest()
        canonical_headers = (f"host:{self.host}\n"
                             f"x-amz-content-sha256:{payload_hash}\n"
                             f"x-amz-date:{amzdate}\n")
        signed_headers = "host;x-amz-content-sha256;x-amz-date"
        canonical_request = (f"{method}\n{canonical_uri}\n{query}\n"
                             f"{canonical_headers}\n{signed_headers}\n{payload_hash}")
        algorithm = "AWS4-HMAC-SHA256"
        cred_scope = f"{datestamp}/{self.region}/s3/aws4_request"
        string_to_sign = (f"{algorithm}\n{amzdate}\n{cred_scope}\n"
                          f"{hashlib.sha256(canonical_request.encode()).hexdigest()}")
        signature = hmac.new(self._signing_key(datestamp),
                             string_to_sign.encode(), hashlib.sha256).hexdigest()
        auth = (f"{algorithm} Credential={self.access_key}/{cred_scope}, "
                f"SignedHeaders={signed_headers}, Signature={signature}")
        headers = {"Authorization": auth, "x-amz-date": amzdate,
                   "x-amz-content-sha256": payload_hash}
        url = f"{self.endpoint}{canonical_uri}?{query}"
        return requests.request(method, url, headers=headers)

    def delete_prefix(self, prefix, min_size=0):
        """Delete every object under prefix, one at a time (no bulk delete → no
        Content-MD5 requirement). Returns count deleted."""
        keys = self.list(prefix, min_size=min_size)
        n = 0
        for k in keys:
            try:
                self.delete(k); n += 1
            except Exception as e:
                print(f"  delete {k} failed: {str(e)[:80]}")
        return n

    # ---- convenience for parquet (optional, needs pyarrow) ----
    def put_parquet_table(self, path, table):
        import pyarrow.parquet as pq
        buf = io.BytesIO()
        pq.write_table(table, buf)
        return self.put_bytes(path, buf.getvalue())

    def get_parquet_table(self, path):
        import pyarrow.parquet as pq
        return pq.read_table(io.BytesIO(self.get_bytes(path)))
