# Event Catalog

| Event | Producer | Consumer | Notes |
|---|---|---|---|
| `user_logged_in` | IAM | Analytics, audit trail | Updates active session state. |
| `notification_created` | Notification service | Websocket, push, email, SMS | Fan-out respects channel preferences. |
| `device_registered` | Client app | Notification registry | Stores push reachability for a device. |
| `payment_initiated` | Finance module | Provider adapter, analytics | Tracks checkout lifecycle. |
| `invoice_monthly_generated` | Billing scheduler | Notifications, finance ledger | Raised for each active tenancy billing cycle. |
| `payment_reminder_scheduled` | Reminder scheduler | Notification service | Creates T-7/T-3/T-1 reminders per policy. |
| `payment_received` | Payment webhook handler | Notifications, analytics, landlord dashboard | Marks payable as settled and suppresses future reminders. |
| `invoice_overdue` | Billing scheduler | Notification service, collections workflow | Triggers late fee and escalation notifications. |
| `utility_bill_uploaded` | Owner/manager billing UI | Billing module, audit log | Contains attachment, amount, due date, period metadata. |
| `utility_bill_split_published` | Billing module | Tenant inbox, notifications | Emits tenant-level payable amounts after split validation. |
| `utility_bill_dispute_opened` | Tenant app | Owner/manager workflow, admin mediation | Starts bill-level discussion and resolution trail. |
| `maintenance_request_created` | Tenant/owner/manager app | Assignment engine, notifications | Created with severity, category, and evidence attachments. |
| `maintenance_status_changed` | Maintenance module | Tenant inbox, owner dashboard | Captures assignment, in-progress, completion, reopen events. |
| `operations_task_due` | Operations scheduler | Assigned staff, owner/manager | Preventive workflow reminder before SLA breach. |
| `operations_task_overdue` | Operations scheduler | Owner/manager escalation channel | Raised when preventive workflow SLA is breached. |
| `system_capabilities_requested` | Web or mobile client | System API | Drives capability-based UI. |
