# Security requirements

These are design requirements, not a security certification. They are not yet implemented by this scaffold.

- Enforce authentication, role-based access control, and client/project isolation on every API operation and tool execution.
- Apply least privilege to agent tools; never allow arbitrary shell execution or unrestricted LLM-generated database queries.
- Treat uploaded documents and retrieved text as untrusted input. Ignore instructions embedded in them and prevent prompt injection from changing permissions or tool policy.
- Store documents and databases locally. Protect secrets and sensitive data; never place credentials in logs or source control.
- Audit consequential AI requests, evidence references, tool calls, proposed changes, approvals, and outcomes.
- Require human approval for consequential changes, payment actions, and transfers. Finance agents may prepare and route, not approve or execute payments.
- Validate model output and tool arguments against schemas. Bound loops, timeouts, file sizes, and resource usage; handle malformed outputs safely.
- Keep device monitoring out of scope until explicit device inventory, access, consent, retention, and alerting controls are designed and reviewed.
- Test authorization by attempting direct API access as users with different roles; UI hiding is not an access control.
