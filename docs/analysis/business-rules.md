# Business Rules

1. Module flags determine whether routers, UI navigation, and runtime behavior are available.
2. Provider selection is environment-driven and does not require database changes.
3. Notification delivery must respect both user preferences and provider readiness.
4. A user may hold multiple active notification devices across providers and platforms.
5. Public push configuration must expose only client-safe values.
6. System discovery endpoints must remain available even when optional modules are disabled.
7. Long-term tenancies must use recurring monthly rent schedules, with proration only for partial first/last months.
8. Monthly invoice due dates, grace periods, and late-fee start windows are configurable at property or tenancy level.
9. Reminder notifications for payable items (rent and utility bill shares) must stop once the payable becomes fully settled.
10. Utility bill sharing requires attachment evidence (image/PDF) and split validation before publication to tenants.
11. A utility bill split can be assigned to one tenant (100%) or multiple tenants (equal/percentage/fixed), but total allocations must reconcile to the payable total.
12. Tenants must be able to view bill evidence, split basis, and payable history before making payment.
13. Overdue payment escalation must notify tenant and owner/manager, and may optionally include backup contacts.
14. Maintenance requests may be created by tenant, owner, or manager; assignment/completion approvals remain owner/manager controlled.
15. Preventive operations tasks (meter readings, routine inspections, compliance checks) follow SLA timelines and generate escalation events when overdue.
