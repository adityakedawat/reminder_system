-- test_data.sql: Generate test data for Reminder System

-- 1. Insert a test client
INSERT INTO public.clients (first_name, last_name, email, mobile, company_name, company_type, gst_no, address)
VALUES ('Test', 'User', 'testuser@example.com', 1234567890, 'Test Company', 'Private', 'GST1234', '123 Test St')
RETURNING id;

-- 2. Insert a test client group
INSERT INTO public.client_groups (group_code, group_name, comments)
VALUES ('TESTGRP', 'Test Group', 'Test group for reminders')
RETURNING group_id;

-- 3. Map the client to the group
INSERT INTO public.client_group_map (group_id, client_id)
VALUES (
    (SELECT group_id FROM public.client_groups WHERE group_code = 'TESTGRP'),
    (SELECT id FROM public.clients WHERE email = 'testuser@example.com')
);

-- 4. Insert a test email template
INSERT INTO public.email_template (subject, body, external_reference_info, name, data_references)
VALUES (
    'Test Reminder: {{reminder_type}} due on {{deadline}}',
    '<p>Hello {{client_name}},<br>Your {{reminder_type}} is due on {{deadline}} ({{days_until_deadline}} days left).</p>',
    'Test reference',
    'Test Template',
    ARRAY['client_name', 'reminder_type', 'deadline', 'days_until_deadline']
)
RETURNING template_id;

-- 5. Insert a test reminder type
INSERT INTO public.reminder_type_info (email_template_id, name)
VALUES (
    (SELECT template_id FROM public.email_template WHERE name = 'Test Template'),
    'Test Reminder Type'
)
RETURNING reminder_type_id;

-- 6. Insert a test reminder for the client (deadline 7 days from today, reminder 7 and 3 days before)
INSERT INTO public.reminder_info (reminder_type_id, deadline, days_before_deadline, client_id, group_id)
VALUES (
    (SELECT reminder_type_id FROM public.reminder_type_info WHERE name = 'Test Reminder Type'),
    CURRENT_DATE + INTERVAL '7 days',
    ARRAY[7, 3],
    (SELECT id FROM public.clients WHERE email = 'testuser@example.com'),
    (SELECT group_id FROM public.client_groups WHERE group_code = 'TESTGRP')
)
RETURNING reminder_id;

-- 7. Insert a test lead
INSERT INTO public.leads (name, issue_description, mobile, email, client_id)
VALUES (
    'Test Lead',
    'Test issue description',
    9876543210,
    'lead@example.com',
    (SELECT id FROM public.clients WHERE email = 'testuser@example.com')
);

-- 8. (Optional) Insert a test blocklist entry (to test blocklist logic)
-- Uncomment to test blocklist
-- INSERT INTO public.reminder_blocklist (client_id, reason)
-- VALUES ((SELECT id FROM public.clients WHERE email = 'testuser@example.com'), 'Testing blocklist');

-- 9. (Optional) Insert a test unsubscribe entry (to test unsubscribe logic)
-- Uncomment to test unsubscribe
-- INSERT INTO public.reminder_unsubscribers (reminder_id, client_id, reason_type, reason)
-- VALUES (
--   (SELECT reminder_id FROM public.reminder_info LIMIT 1),
--   (SELECT id FROM public.clients WHERE email = 'testuser@example.com'),
--   'Test',
--   'Testing unsubscribe'
-- ); 