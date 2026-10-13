# Business guide

## Purpose

WEB-PAYM will progressively centralize the recording, validation, and
administrative consolidation of payments currently managed through Excel files.
It will not execute bank transfers at this stage.

## Available today

This phase provides the technical foundation and a welcome page. Signing in,
managing users, viewing receipts, and recording payments are not available yet.
The access model is documented for implementation in the next phase.
All application content and documentation use English.

## Understanding access

The primary purpose of roles and permissions is to determine **which views each
person can access**. Some people may access analytics while others cannot;
some may view receipts while others cannot. Actions within those views can also
be separated when needed: view, create, update, approve, or export.

| Concept | Business meaning |
| --- | --- |
| User | A person with an individual account |
| Team | A work group a person can belong to |
| Module | A functional section, such as future energy payment management |
| Role | A configurable collection of access rights shared by people |
| Permission | Authorization to view a section or perform an action |
| Scope | All teams or one specific team |

Roles are not fixed job titles embedded in code. Roles can be created, expanded,
or have permissions removed without redesigning authentication. A person can
hold multiple roles and belong to multiple teams.

## Illustrative examples, not approved process rules

| Future need | Possible configuration |
| --- | --- |
| A group can view analytics | Grant `analytics.view` to one of its roles |
| Another group cannot view analytics | Omit that permission from its roles |
| A person can view receipts but cannot edit them | Grant `receipts.view` without `receipts.update` |
| Open a view to all current users | Assign a shared role containing that permission |
| Limit a view to one team's information | Assign the role with that team's scope |

`analytics` and `receipts` are examples: they are not operational modules yet,
and their relationship to payments or energy has not been decided.

If common access for new accounts is adopted, account creation must explicitly
assign the shared role. New permissions are not inherited automatically, and
having an account does not automatically enable every view.

## Initial flexibility

Start with a small number of roles and broad permissions as views are approved.
The foundation supports finer controls later. Approval hierarchies, amount
limits, record ownership, and energy workflows are not defined yet. There is
no switch that bypasses all server authorization checks.

Removing a permission from one role does not remove grants from other roles.
A person retains access if another role still grants it. The effective
permissions view will show combined grants and their scope for review.

## Information security

Hiding a menu item is insufficient: the server must check permissions before
returning data, including future analytics and receipt content. Protected data
must not be downloaded merely to hide it on screen.

Deactivating an account will prevent access and revoke its sessions. Role,
membership, and permission changes will be audited. Administrators will manage
access through specific permissions, initially requiring global scope.

## Open business decisions

- Final catalog of views and modules.
- Initial profiles and organization-wide common access.
- Which views show global information and which depend on a team.
- Whether viewing a receipt also permits downloading it; these can be separate permissions.
- Whether global analytics include teams outside a person's data scope.
- Energy workflow, responsible parties, and approvals.
- Audit and document retention policies.

These decisions do not block repository setup. Resolve each before implementing
the affected capability.
