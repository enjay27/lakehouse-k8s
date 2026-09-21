---
description: Compare a release's intended values against what is actually running
---
For the release named in $ARGUMENTS, establish what is *in effect* -- not what
was intended.

1. `kubectl config current-context` must be exactly `orbstack`. Anything else:
   halt and ask.
2. `helm -n datahub-hynix get values <release>` and, for the previous
   revision, `--revision N`. The diff between revisions turns "what did I
   break" into a fact rather than a guess.
3. **Never confirm a setting by reading the values file.** Query the running
   object and compare against the *chart default*. A value that matches the
   default is not evidence -- it is indistinguishable from a block that was
   never applied. This is exactly how Fault 1 hid for months: an entire
   `postgresql:` block sat at the wrong nesting level while the cluster served
   subchart defaults.
4. For `charts/postgresql/`, remember it is an umbrella chart -- anything meant
   for the subchart must be nested under `postgresql-ha:` or Helm silently
   ignores it.
5. Report intended vs in-effect vs chart-default as three separate columns.
