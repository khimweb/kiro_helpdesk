CREATE TABLE "accounts_user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "last_login" datetime NULL, "is_superuser" bool NOT NULL, "username" varchar(150) NOT NULL UNIQUE, "first_name" varchar(150) NOT NULL, "last_name" varchar(150) NOT NULL, "email" varchar(254) NOT NULL, "is_staff" bool NOT NULL, "is_active" bool NOT NULL, "date_joined" datetime NOT NULL, "phone" varchar(20) NULL, "profile_picture" varchar(100) NULL, "department" varchar(100) NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "role" varchar(20) NOT NULL);

CREATE TABLE "accounts_user_groups" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" bigint NOT NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "accounts_user_user_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" bigint NOT NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "auth_group" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(150) NOT NULL UNIQUE);

CREATE TABLE "auth_group_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "auth_permission" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "codename" varchar(100) NOT NULL, "name" varchar(255) NOT NULL);

CREATE TABLE "django_admin_log" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "object_id" text NULL, "object_repr" varchar(200) NOT NULL, "action_flag" smallint unsigned NOT NULL CHECK ("action_flag" >= 0), "change_message" text NOT NULL, "content_type_id" integer NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" bigint NOT NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED, "action_time" datetime NOT NULL);

CREATE TABLE "django_content_type" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app_label" varchar(100) NOT NULL, "model" varchar(100) NOT NULL);

CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(255) NOT NULL, "applied" datetime NOT NULL);

CREATE TABLE "django_session" ("session_key" varchar(40) NOT NULL PRIMARY KEY, "session_data" text NOT NULL, "expire_date" datetime NOT NULL);

CREATE TABLE sqlite_sequence(name,seq);

CREATE TABLE "tickets_aichatmessage" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "role" varchar(20) NOT NULL, "content" text NOT NULL, "created_at" datetime NOT NULL, "session_id" bigint NOT NULL REFERENCES "tickets_aichatsession" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "tickets_aichatsession" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(200) NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "user_id" bigint NOT NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "tickets_attachment" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "file" varchar(100) NOT NULL, "uploaded_at" datetime NOT NULL, "ticket_id" bigint NOT NULL REFERENCES "tickets_ticket" ("id") DEFERRABLE INITIALLY DEFERRED, "uploaded_by_id" bigint NOT NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "tickets_category" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(100) NOT NULL UNIQUE, "description" text NOT NULL, "created_at" datetime NOT NULL);

CREATE TABLE "tickets_commentattachment" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "file" varchar(100) NOT NULL, "uploaded_at" datetime NOT NULL, "comment_id" bigint NOT NULL REFERENCES "tickets_ticketcomment" ("id") DEFERRABLE INITIALLY DEFERRED, "uploaded_by_id" bigint NOT NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "tickets_sla" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "priority" varchar(10) NOT NULL UNIQUE, "response_time_hours" integer unsigned NOT NULL CHECK ("response_time_hours" >= 0), "resolution_time_hours" integer unsigned NOT NULL CHECK ("resolution_time_hours" >= 0), "is_active" bool NOT NULL);

CREATE TABLE "tickets_ticket" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "ticket_id" varchar(20) NOT NULL UNIQUE, "title" varchar(255) NOT NULL, "description" text NOT NULL, "priority" varchar(10) NOT NULL, "status" varchar(15) NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "resolved_at" datetime NULL, "closed_at" datetime NULL, "sla_deadline" datetime NULL, "rating" integer NULL, "rating_comment" text NULL, "assigned_to_id" bigint NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED, "category_id" bigint NULL REFERENCES "tickets_category" ("id") DEFERRABLE INITIALLY DEFERRED, "created_by_id" bigint NOT NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "tickets_ticketassignment" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "admin_checked" bool NOT NULL, "admin_checked_at" datetime NULL, "assigned_to_manager_at" datetime NULL, "manager_checked" bool NOT NULL, "manager_checked_at" datetime NULL, "assigned_to_it_staff_at" datetime NULL, "it_staff_completed" bool NOT NULL, "it_staff_completed_at" datetime NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "admin_checked_by_id" bigint NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED, "assigned_to_it_staff_id" bigint NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED, "assigned_to_manager_id" bigint NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED, "it_staff_completed_by_id" bigint NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED, "manager_checked_by_id" bigint NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED, "ticket_id" bigint NOT NULL UNIQUE REFERENCES "tickets_ticket" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "tickets_ticketcomment" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "content" text NOT NULL, "is_internal" bool NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "ticket_id" bigint NOT NULL REFERENCES "tickets_ticket" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" bigint NOT NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "tickets_tickethistory" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "action" varchar(100) NOT NULL, "description" text NOT NULL, "created_at" datetime NOT NULL, "ticket_id" bigint NOT NULL REFERENCES "tickets_ticket" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" bigint NOT NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE INDEX "accounts_user_groups_group_id_bd11a704" ON "accounts_user_groups" ("group_id");

CREATE INDEX "accounts_user_groups_user_id_52b62117" ON "accounts_user_groups" ("user_id");

CREATE UNIQUE INDEX "accounts_user_groups_user_id_group_id_59c0b32f_uniq" ON "accounts_user_groups" ("user_id", "group_id");

CREATE INDEX "accounts_user_user_permissions_permission_id_113bb443" ON "accounts_user_user_permissions" ("permission_id");

CREATE INDEX "accounts_user_user_permissions_user_id_e4f0a161" ON "accounts_user_user_permissions" ("user_id");

CREATE UNIQUE INDEX "accounts_user_user_permissions_user_id_permission_id_2ab516c2_uniq" ON "accounts_user_user_permissions" ("user_id", "permission_id");

CREATE INDEX "auth_group_permissions_group_id_b120cbf9" ON "auth_group_permissions" ("group_id");

CREATE UNIQUE INDEX "auth_group_permissions_group_id_permission_id_0cd325b0_uniq" ON "auth_group_permissions" ("group_id", "permission_id");

CREATE INDEX "auth_group_permissions_permission_id_84c5c92e" ON "auth_group_permissions" ("permission_id");

CREATE INDEX "auth_permission_content_type_id_2f476e4b" ON "auth_permission" ("content_type_id");

CREATE UNIQUE INDEX "auth_permission_content_type_id_codename_01ab375a_uniq" ON "auth_permission" ("content_type_id", "codename");

CREATE INDEX "django_admin_log_content_type_id_c4bce8eb" ON "django_admin_log" ("content_type_id");

CREATE INDEX "django_admin_log_user_id_c564eba6" ON "django_admin_log" ("user_id");

CREATE UNIQUE INDEX "django_content_type_app_label_model_76bd3d3b_uniq" ON "django_content_type" ("app_label", "model");

CREATE INDEX "django_session_expire_date_a5c62663" ON "django_session" ("expire_date");

CREATE INDEX "tickets_aichatmessage_session_id_ba00fa5c" ON "tickets_aichatmessage" ("session_id");

CREATE INDEX "tickets_aichatsession_user_id_71bab74f" ON "tickets_aichatsession" ("user_id");

CREATE INDEX "tickets_attachment_ticket_id_00f5c87f" ON "tickets_attachment" ("ticket_id");

CREATE INDEX "tickets_attachment_uploaded_by_id_1e22a000" ON "tickets_attachment" ("uploaded_by_id");

CREATE INDEX "tickets_commentattachment_comment_id_e73b2c37" ON "tickets_commentattachment" ("comment_id");

CREATE INDEX "tickets_commentattachment_uploaded_by_id_77902332" ON "tickets_commentattachment" ("uploaded_by_id");

CREATE INDEX "tickets_ticket_assigned_to_id_142e13bf" ON "tickets_ticket" ("assigned_to_id");

CREATE INDEX "tickets_ticket_category_id_710dbfd0" ON "tickets_ticket" ("category_id");

CREATE INDEX "tickets_ticket_created_by_id_c418a145" ON "tickets_ticket" ("created_by_id");

CREATE INDEX "tickets_ticketassignment_admin_checked_by_id_33b8fce9" ON "tickets_ticketassignment" ("admin_checked_by_id");

CREATE INDEX "tickets_ticketassignment_assigned_to_it_staff_id_46e77a30" ON "tickets_ticketassignment" ("assigned_to_it_staff_id");

CREATE INDEX "tickets_ticketassignment_assigned_to_manager_id_9e745758" ON "tickets_ticketassignment" ("assigned_to_manager_id");

CREATE INDEX "tickets_ticketassignment_it_staff_completed_by_id_8721da4c" ON "tickets_ticketassignment" ("it_staff_completed_by_id");

CREATE INDEX "tickets_ticketassignment_manager_checked_by_id_3ffb729c" ON "tickets_ticketassignment" ("manager_checked_by_id");

CREATE INDEX "tickets_ticketcomment_ticket_id_ef1ee786" ON "tickets_ticketcomment" ("ticket_id");

CREATE INDEX "tickets_ticketcomment_user_id_2e09e51f" ON "tickets_ticketcomment" ("user_id");

CREATE INDEX "tickets_tickethistory_ticket_id_fb0c86a4" ON "tickets_tickethistory" ("ticket_id");

CREATE INDEX "tickets_tickethistory_user_id_7560d939" ON "tickets_tickethistory" ("user_id");

