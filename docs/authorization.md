# Planned authorization model

Status: approved design incorporating the user's clarification of 2026-10-13.
Implementation belongs to Phase C. Phase B has no operational authorization.

## Views and actions

A permission is a catalog entry `(module_id, action)`, exposed as
`module.code + '.' + action`. `view` permits access to a section and its data;
other actions are added as defined. Do not add a boolean column per view to
`users` or make access conditional on role names.

A future view may require `analytics.view` or `receipts.view`. Subsections may
use actions such as `receipts_view` within `energy`, or a separate module,
depending on the agreed functional boundary. Use stable codes with a single
period separating the module and action.

Creating a permission does not implement a view: the frontend route, endpoint,
backend check, and tests must exist. The dynamic catalog avoids changes to the
authentication core; each feature declares its required permission.

## Positive grants

Permissions combine by union within each scope. This version has no explicit
denials, role priorities, or direct per-user permissions.

A global assignment covers all teams. A team assignment covers only that team
and requires active membership. Scope is not inferred from the role name.
A team permission does not authorize management of the global catalog.

Navigation displays an entry when an applicable grant exists, but data queries
are filtered by effective scope. A team selector cannot expand permissions.
Queries, aggregations, counts, and future downloads must apply the same filters;
never filter only after delivering data to the client.

## Applying or removing restrictions

Broad access is configured by assigning a shared role with the desired
permissions. Restricting a view means removing the grant or narrowing its scope.
There is no permissive mode that disables server checks.

Removing a permission from one role leaves grants from other roles intact.
The effective permissions UI must explain the source of each grant. Disabling
a module prevents its operations regardless of existing grants.

## Administrative security

The first version requires global permissions to create users, manage and
assign roles, and change memberships. Proposed explicit actions:
`users.view/create/update/deactivate`, `roles.view/create/update/assign`,
`teams.view/create/update/memberships_manage`, `modules.view/manage`, and
`dashboard.view`. Assignment revocation uses `roles.assign`; editing a role's
permissions requires `roles.update`.

Changes are transactional and audited. Delegation rules for team administrators
to grant permissions remain undefined and must not be inferred.

## Future sessions

Argon2id; random opaque tokens stored as hashes; HttpOnly cookies with
SameSite=Lax and Secure in production; CSRF and origin checks; absolute and
idle expiration. Permission changes take effect on the next request without
requiring another login. No authentication tokens in localStorage.

Shared account/IP login limits use PostgreSQL. Failed authentication events
must not record passwords or cookies, and messages must not reveal account
existence. The local credential provider remains separate from session issuance
to support future corporate SSO integration.
