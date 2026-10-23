# Evidence

Copies of the artifacts produced by the workflow, kept in the repository
because Actions artifacts expire.

| File | Origin |
| --- | --- |
| `pr_report.md` | `verified/pr_report.md` of run [39927537759](https://github.com/CharlesSBL/taskly-app/actions/runs/39927537759) (demo PR [#11](https://github.com/CharlesSBL/taskly-app/pull/11)), the exact text posted as the sticky comment |
| `verification_report.json` | `verified/verification_report.json` of the same run: accepted stacks, coverage, differential result and patch sha256 |
| `agent_trace.trimmed.json` | `artifacts/agent_trace.json` of the same run, with tool results truncated to 200 characters |

The untrusted artifacts are uploaded before verification and the verified
directory is produced by the gate job, so the two trees are separate in the
run. The full files can be regenerated from any later run of the agent.
