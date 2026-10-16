--
-- PostgreSQL database dump
--

\restrict b4v5cAgVdqw59ecKZz4KJFvhxtRLP8aeWcPfbJdO6IWfdPbOF8SOI4ltSI0bcec

-- Dumped from database version 16.14
-- Dumped by pg_dump version 16.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: hive
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO hive;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: hive
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: AUX_TABLE; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."AUX_TABLE" (
    "MT_KEY1" character varying(128) NOT NULL,
    "MT_KEY2" bigint NOT NULL,
    "MT_COMMENT" character varying(255)
);


ALTER TABLE public."AUX_TABLE" OWNER TO hive;

--
-- Name: BUCKETING_COLS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."BUCKETING_COLS" (
    "SD_ID" bigint NOT NULL,
    "BUCKET_COL_NAME" character varying(256) DEFAULT NULL::character varying,
    "INTEGER_IDX" bigint NOT NULL
);


ALTER TABLE public."BUCKETING_COLS" OWNER TO hive;

--
-- Name: CATALOG_PARAMS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."CATALOG_PARAMS" (
    "CTLG_ID" bigint NOT NULL,
    "PARAM_KEY" character varying(180) NOT NULL,
    "PARAM_VALUE" character varying(4000) DEFAULT NULL::character varying
);


ALTER TABLE public."CATALOG_PARAMS" OWNER TO hive;

--
-- Name: CDS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."CDS" (
    "CD_ID" bigint NOT NULL
);


ALTER TABLE public."CDS" OWNER TO hive;

--
-- Name: COLUMNS_V2; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."COLUMNS_V2" (
    "CD_ID" bigint NOT NULL,
    "COMMENT" character varying(4000),
    "COLUMN_NAME" character varying(767) NOT NULL,
    "TYPE_NAME" text,
    "INTEGER_IDX" integer NOT NULL
);


ALTER TABLE public."COLUMNS_V2" OWNER TO hive;

--
-- Name: COMPACTION_METRICS_CACHE; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."COMPACTION_METRICS_CACHE" (
    "CMC_DATABASE" character varying(128) NOT NULL,
    "CMC_TABLE" character varying(256) NOT NULL,
    "CMC_PARTITION" character varying(767),
    "CMC_METRIC_TYPE" character varying(128) NOT NULL,
    "CMC_METRIC_VALUE" integer NOT NULL,
    "CMC_VERSION" integer NOT NULL
);


ALTER TABLE public."COMPACTION_METRICS_CACHE" OWNER TO hive;

--
-- Name: COMPACTION_QUEUE; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."COMPACTION_QUEUE" (
    "CQ_ID" bigint NOT NULL,
    "CQ_DATABASE" character varying(128) NOT NULL,
    "CQ_TABLE" character varying(256) NOT NULL,
    "CQ_PARTITION" character varying(767),
    "CQ_STATE" character(1) NOT NULL,
    "CQ_TYPE" character(1) NOT NULL,
    "CQ_TBLPROPERTIES" character varying(2048),
    "CQ_WORKER_ID" character varying(128),
    "CQ_ENQUEUE_TIME" bigint,
    "CQ_START" bigint,
    "CQ_RUN_AS" character varying(128),
    "CQ_HIGHEST_WRITE_ID" bigint,
    "CQ_META_INFO" bytea,
    "CQ_HADOOP_JOB_ID" character varying(32),
    "CQ_ERROR_MESSAGE" text,
    "CQ_NEXT_TXN_ID" bigint,
    "CQ_TXN_ID" bigint,
    "CQ_COMMIT_TIME" bigint,
    "CQ_INITIATOR_ID" character varying(128),
    "CQ_INITIATOR_VERSION" character varying(128),
    "CQ_WORKER_VERSION" character varying(128),
    "CQ_CLEANER_START" bigint,
    "CQ_RETRY_RETENTION" bigint DEFAULT 0 NOT NULL,
    "CQ_POOL_NAME" character varying(128),
    "CQ_NUMBER_OF_BUCKETS" integer,
    "CQ_ORDER_BY" character varying(4000)
);


ALTER TABLE public."COMPACTION_QUEUE" OWNER TO hive;

--
-- Name: COMPLETED_COMPACTIONS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."COMPLETED_COMPACTIONS" (
    "CC_ID" bigint NOT NULL,
    "CC_DATABASE" character varying(128) NOT NULL,
    "CC_TABLE" character varying(256) NOT NULL,
    "CC_PARTITION" character varying(767),
    "CC_STATE" character(1) NOT NULL,
    "CC_TYPE" character(1) NOT NULL,
    "CC_TBLPROPERTIES" character varying(2048),
    "CC_WORKER_ID" character varying(128),
    "CC_ENQUEUE_TIME" bigint,
    "CC_START" bigint,
    "CC_END" bigint,
    "CC_RUN_AS" character varying(128),
    "CC_HIGHEST_WRITE_ID" bigint,
    "CC_META_INFO" bytea,
    "CC_HADOOP_JOB_ID" character varying(32),
    "CC_ERROR_MESSAGE" text,
    "CC_NEXT_TXN_ID" bigint,
    "CC_TXN_ID" bigint,
    "CC_COMMIT_TIME" bigint,
    "CC_INITIATOR_ID" character varying(128),
    "CC_INITIATOR_VERSION" character varying(128),
    "CC_WORKER_VERSION" character varying(128),
    "CC_POOL_NAME" character varying(128),
    "CC_NUMBER_OF_BUCKETS" integer,
    "CC_ORDER_BY" character varying(4000)
);


ALTER TABLE public."COMPLETED_COMPACTIONS" OWNER TO hive;

--
-- Name: COMPLETED_TXN_COMPONENTS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."COMPLETED_TXN_COMPONENTS" (
    "CTC_TXNID" bigint NOT NULL,
    "CTC_DATABASE" character varying(128) NOT NULL,
    "CTC_TABLE" character varying(256),
    "CTC_PARTITION" character varying(767),
    "CTC_TIMESTAMP" timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "CTC_WRITEID" bigint,
    "CTC_UPDATE_DELETE" character(1) NOT NULL
);


ALTER TABLE public."COMPLETED_TXN_COMPONENTS" OWNER TO hive;

--
-- Name: CTLGS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."CTLGS" (
    "CTLG_ID" bigint NOT NULL,
    "NAME" character varying(256),
    "DESC" character varying(4000),
    "LOCATION_URI" character varying(4000) NOT NULL,
    "CREATE_TIME" bigint
);


ALTER TABLE public."CTLGS" OWNER TO hive;

--
-- Name: DATABASE_PARAMS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."DATABASE_PARAMS" (
    "DB_ID" bigint NOT NULL,
    "PARAM_KEY" character varying(180) NOT NULL,
    "PARAM_VALUE" character varying(4000) DEFAULT NULL::character varying
);


ALTER TABLE public."DATABASE_PARAMS" OWNER TO hive;

--
-- Name: DATACONNECTORS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."DATACONNECTORS" (
    "NAME" character varying(128) NOT NULL,
    "TYPE" character varying(32) NOT NULL,
    "URL" character varying(4000) NOT NULL,
    "COMMENT" character varying(256),
    "OWNER_NAME" character varying(256),
    "OWNER_TYPE" character varying(10),
    "CREATE_TIME" integer NOT NULL
);


ALTER TABLE public."DATACONNECTORS" OWNER TO hive;

--
-- Name: DATACONNECTOR_PARAMS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."DATACONNECTOR_PARAMS" (
    "NAME" character varying(128) NOT NULL,
    "PARAM_KEY" character varying(180) NOT NULL,
    "PARAM_VALUE" character varying(4000)
);


ALTER TABLE public."DATACONNECTOR_PARAMS" OWNER TO hive;

--
-- Name: DBS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."DBS" (
    "DB_ID" bigint NOT NULL,
    "DESC" character varying(4000) DEFAULT NULL::character varying,
    "DB_LOCATION_URI" character varying(4000) NOT NULL,
    "NAME" character varying(128) DEFAULT NULL::character varying,
    "OWNER_NAME" character varying(128) DEFAULT NULL::character varying,
    "OWNER_TYPE" character varying(10) DEFAULT NULL::character varying,
    "CTLG_NAME" character varying(256) DEFAULT 'hive'::character varying NOT NULL,
    "CREATE_TIME" bigint,
    "DB_MANAGED_LOCATION_URI" character varying(4000),
    "TYPE" character varying(32) DEFAULT 'NATIVE'::character varying NOT NULL,
    "DATACONNECTOR_NAME" character varying(128),
    "REMOTE_DBNAME" character varying(128)
);


ALTER TABLE public."DBS" OWNER TO hive;

--
-- Name: DB_PRIVS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."DB_PRIVS" (
    "DB_GRANT_ID" bigint NOT NULL,
    "CREATE_TIME" bigint NOT NULL,
    "DB_ID" bigint,
    "GRANT_OPTION" smallint NOT NULL,
    "GRANTOR" character varying(128) DEFAULT NULL::character varying,
    "GRANTOR_TYPE" character varying(128) DEFAULT NULL::character varying,
    "PRINCIPAL_NAME" character varying(128) DEFAULT NULL::character varying,
    "PRINCIPAL_TYPE" character varying(128) DEFAULT NULL::character varying,
    "DB_PRIV" character varying(128) DEFAULT NULL::character varying,
    "AUTHORIZER" character varying(128) DEFAULT NULL::character varying
);


ALTER TABLE public."DB_PRIVS" OWNER TO hive;

--
-- Name: DC_PRIVS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."DC_PRIVS" (
    "DC_GRANT_ID" bigint NOT NULL,
    "CREATE_TIME" bigint NOT NULL,
    "NAME" character varying(128),
    "GRANT_OPTION" smallint NOT NULL,
    "GRANTOR" character varying(128) DEFAULT NULL::character varying,
    "GRANTOR_TYPE" character varying(128) DEFAULT NULL::character varying,
    "PRINCIPAL_NAME" character varying(128) DEFAULT NULL::character varying,
    "PRINCIPAL_TYPE" character varying(128) DEFAULT NULL::character varying,
    "DC_PRIV" character varying(128) DEFAULT NULL::character varying,
    "AUTHORIZER" character varying(128) DEFAULT NULL::character varying
);


ALTER TABLE public."DC_PRIVS" OWNER TO hive;

--
-- Name: DELEGATION_TOKENS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."DELEGATION_TOKENS" (
    "TOKEN_IDENT" character varying(767) NOT NULL,
    "TOKEN" character varying(767)
);


ALTER TABLE public."DELEGATION_TOKENS" OWNER TO hive;

--
-- Name: FUNCS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."FUNCS" (
    "FUNC_ID" bigint NOT NULL,
    "CLASS_NAME" character varying(4000),
    "CREATE_TIME" integer NOT NULL,
    "DB_ID" bigint,
    "FUNC_NAME" character varying(128),
    "FUNC_TYPE" integer NOT NULL,
    "OWNER_NAME" character varying(128),
    "OWNER_TYPE" character varying(10)
);


ALTER TABLE public."FUNCS" OWNER TO hive;

--
-- Name: FUNC_RU; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."FUNC_RU" (
    "FUNC_ID" bigint NOT NULL,
    "RESOURCE_TYPE" integer NOT NULL,
    "RESOURCE_URI" character varying(4000),
    "INTEGER_IDX" integer NOT NULL
);


ALTER TABLE public."FUNC_RU" OWNER TO hive;

--
-- Name: GLOBAL_PRIVS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."GLOBAL_PRIVS" (
    "USER_GRANT_ID" bigint NOT NULL,
    "CREATE_TIME" bigint NOT NULL,
    "GRANT_OPTION" smallint NOT NULL,
    "GRANTOR" character varying(128) DEFAULT NULL::character varying,
    "GRANTOR_TYPE" character varying(128) DEFAULT NULL::character varying,
    "PRINCIPAL_NAME" character varying(128) DEFAULT NULL::character varying,
    "PRINCIPAL_TYPE" character varying(128) DEFAULT NULL::character varying,
    "USER_PRIV" character varying(128) DEFAULT NULL::character varying,
    "AUTHORIZER" character varying(128) DEFAULT NULL::character varying
);


ALTER TABLE public."GLOBAL_PRIVS" OWNER TO hive;

--
-- Name: HIVE_LOCKS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."HIVE_LOCKS" (
    "HL_LOCK_EXT_ID" bigint NOT NULL,
    "HL_LOCK_INT_ID" bigint NOT NULL,
    "HL_TXNID" bigint NOT NULL,
    "HL_DB" character varying(128) NOT NULL,
    "HL_TABLE" character varying(256),
    "HL_PARTITION" character varying(767) DEFAULT NULL::character varying,
    "HL_LOCK_STATE" character(1) NOT NULL,
    "HL_LOCK_TYPE" character(1) NOT NULL,
    "HL_LAST_HEARTBEAT" bigint NOT NULL,
    "HL_ACQUIRED_AT" bigint,
    "HL_USER" character varying(128) NOT NULL,
    "HL_HOST" character varying(128) NOT NULL,
    "HL_HEARTBEAT_COUNT" integer,
    "HL_AGENT_INFO" character varying(128),
    "HL_BLOCKEDBY_EXT_ID" bigint,
    "HL_BLOCKEDBY_INT_ID" bigint
);


ALTER TABLE public."HIVE_LOCKS" OWNER TO hive;

--
-- Name: I_SCHEMA; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."I_SCHEMA" (
    "SCHEMA_ID" bigint NOT NULL,
    "SCHEMA_TYPE" integer NOT NULL,
    "NAME" character varying(256),
    "DB_ID" bigint,
    "COMPATIBILITY" integer NOT NULL,
    "VALIDATION_LEVEL" integer NOT NULL,
    "CAN_EVOLVE" boolean NOT NULL,
    "SCHEMA_GROUP" character varying(256),
    "DESCRIPTION" character varying(4000)
);


ALTER TABLE public."I_SCHEMA" OWNER TO hive;

--
-- Name: KEY_CONSTRAINTS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."KEY_CONSTRAINTS" (
    "CHILD_CD_ID" bigint,
    "CHILD_INTEGER_IDX" bigint,
    "CHILD_TBL_ID" bigint,
    "PARENT_CD_ID" bigint,
    "PARENT_INTEGER_IDX" bigint NOT NULL,
    "PARENT_TBL_ID" bigint NOT NULL,
    "POSITION" bigint NOT NULL,
    "CONSTRAINT_NAME" character varying(400) NOT NULL,
    "CONSTRAINT_TYPE" smallint NOT NULL,
    "UPDATE_RULE" smallint,
    "DELETE_RULE" smallint,
    "ENABLE_VALIDATE_RELY" smallint NOT NULL,
    "DEFAULT_VALUE" character varying(400)
);


ALTER TABLE public."KEY_CONSTRAINTS" OWNER TO hive;

--
-- Name: MASTER_KEYS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."MASTER_KEYS" (
    "KEY_ID" integer NOT NULL,
    "MASTER_KEY" character varying(767)
);


ALTER TABLE public."MASTER_KEYS" OWNER TO hive;

--
-- Name: MASTER_KEYS_KEY_ID_seq; Type: SEQUENCE; Schema: public; Owner: hive
--

CREATE SEQUENCE public."MASTER_KEYS_KEY_ID_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."MASTER_KEYS_KEY_ID_seq" OWNER TO hive;

--
-- Name: MASTER_KEYS_KEY_ID_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hive
--

ALTER SEQUENCE public."MASTER_KEYS_KEY_ID_seq" OWNED BY public."MASTER_KEYS"."KEY_ID";


--
-- Name: MATERIALIZATION_REBUILD_LOCKS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."MATERIALIZATION_REBUILD_LOCKS" (
    "MRL_TXN_ID" bigint NOT NULL,
    "MRL_DB_NAME" character varying(128) NOT NULL,
    "MRL_TBL_NAME" character varying(256) NOT NULL,
    "MRL_LAST_HEARTBEAT" bigint NOT NULL
);


ALTER TABLE public."MATERIALIZATION_REBUILD_LOCKS" OWNER TO hive;

--
-- Name: METASTORE_DB_PROPERTIES; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."METASTORE_DB_PROPERTIES" (
    "PROPERTY_KEY" character varying(255) NOT NULL,
    "PROPERTY_VALUE" character varying(1000) NOT NULL,
    "DESCRIPTION" character varying(1000),
    "PROPERTYCONTENT" bytea
);


ALTER TABLE public."METASTORE_DB_PROPERTIES" OWNER TO hive;

--
-- Name: MIN_HISTORY_LEVEL; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."MIN_HISTORY_LEVEL" (
    "MHL_TXNID" bigint NOT NULL,
    "MHL_MIN_OPEN_TXNID" bigint NOT NULL
);


ALTER TABLE public."MIN_HISTORY_LEVEL" OWNER TO hive;

--
-- Name: MIN_HISTORY_WRITE_ID; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."MIN_HISTORY_WRITE_ID" (
    "MH_TXNID" bigint NOT NULL,
    "MH_DATABASE" character varying(128) NOT NULL,
    "MH_TABLE" character varying(256) NOT NULL,
    "MH_WRITEID" bigint NOT NULL
);


ALTER TABLE public."MIN_HISTORY_WRITE_ID" OWNER TO hive;

--
-- Name: MV_CREATION_METADATA; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."MV_CREATION_METADATA" (
    "MV_CREATION_METADATA_ID" bigint NOT NULL,
    "CAT_NAME" character varying(256) NOT NULL,
    "DB_NAME" character varying(128) NOT NULL,
    "TBL_NAME" character varying(256) NOT NULL,
    "TXN_LIST" text,
    "MATERIALIZATION_TIME" bigint NOT NULL
);


ALTER TABLE public."MV_CREATION_METADATA" OWNER TO hive;

--
-- Name: MV_TABLES_USED; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."MV_TABLES_USED" (
    "MV_CREATION_METADATA_ID" bigint NOT NULL,
    "TBL_ID" bigint NOT NULL,
    "INSERTED_COUNT" bigint DEFAULT 0 NOT NULL,
    "UPDATED_COUNT" bigint DEFAULT 0 NOT NULL,
    "DELETED_COUNT" bigint DEFAULT 0 NOT NULL
);


ALTER TABLE public."MV_TABLES_USED" OWNER TO hive;

--
-- Name: NEXT_COMPACTION_QUEUE_ID; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."NEXT_COMPACTION_QUEUE_ID" (
    "NCQ_NEXT" bigint NOT NULL
);


ALTER TABLE public."NEXT_COMPACTION_QUEUE_ID" OWNER TO hive;

--
-- Name: NEXT_LOCK_ID; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."NEXT_LOCK_ID" (
    "NL_NEXT" bigint NOT NULL
);


ALTER TABLE public."NEXT_LOCK_ID" OWNER TO hive;

--
-- Name: NEXT_WRITE_ID; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."NEXT_WRITE_ID" (
    "NWI_DATABASE" character varying(128) NOT NULL,
    "NWI_TABLE" character varying(256) NOT NULL,
    "NWI_NEXT" bigint NOT NULL
);


ALTER TABLE public."NEXT_WRITE_ID" OWNER TO hive;

--
-- Name: NOTIFICATION_LOG; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."NOTIFICATION_LOG" (
    "NL_ID" bigint NOT NULL,
    "EVENT_ID" bigint NOT NULL,
    "EVENT_TIME" integer NOT NULL,
    "EVENT_TYPE" character varying(32) NOT NULL,
    "CAT_NAME" character varying(256),
    "DB_NAME" character varying(128),
    "TBL_NAME" character varying(256),
    "MESSAGE" text,
    "MESSAGE_FORMAT" character varying(16)
);


ALTER TABLE public."NOTIFICATION_LOG" OWNER TO hive;

--
-- Name: NOTIFICATION_SEQUENCE; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."NOTIFICATION_SEQUENCE" (
    "NNI_ID" bigint NOT NULL,
    "NEXT_EVENT_ID" bigint NOT NULL,
    CONSTRAINT "ONE_ROW_CONSTRAINT" CHECK (("NNI_ID" = 1))
);


ALTER TABLE public."NOTIFICATION_SEQUENCE" OWNER TO hive;

--
-- Name: NUCLEUS_TABLES; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."NUCLEUS_TABLES" (
    "CLASS_NAME" character varying(128) NOT NULL,
    "TABLE_NAME" character varying(128) NOT NULL,
    "TYPE" character varying(4) NOT NULL,
    "OWNER" character varying(2) NOT NULL,
    "VERSION" character varying(20) NOT NULL,
    "INTERFACE_NAME" character varying(255) DEFAULT NULL::character varying
);


ALTER TABLE public."NUCLEUS_TABLES" OWNER TO hive;

--
-- Name: PACKAGES; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."PACKAGES" (
    "PKG_ID" bigint NOT NULL,
    "CREATE_TIME" integer NOT NULL,
    "DB_ID" bigint NOT NULL,
    "NAME" character varying(256) NOT NULL,
    "OWNER_NAME" character varying(128) NOT NULL,
    "HEADER" text NOT NULL,
    "BODY" text NOT NULL
);


ALTER TABLE public."PACKAGES" OWNER TO hive;

--
-- Name: PARTITIONS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."PARTITIONS" (
    "PART_ID" bigint NOT NULL,
    "CREATE_TIME" bigint NOT NULL,
    "LAST_ACCESS_TIME" bigint NOT NULL,
    "PART_NAME" character varying(767) DEFAULT NULL::character varying,
    "SD_ID" bigint,
    "TBL_ID" bigint,
    "WRITE_ID" bigint DEFAULT 0
);


ALTER TABLE public."PARTITIONS" OWNER TO hive;

--
-- Name: PARTITION_EVENTS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."PARTITION_EVENTS" (
    "PART_NAME_ID" bigint NOT NULL,
    "CAT_NAME" character varying(256),
    "DB_NAME" character varying(128),
    "EVENT_TIME" bigint NOT NULL,
    "EVENT_TYPE" integer NOT NULL,
    "PARTITION_NAME" character varying(767),
    "TBL_NAME" character varying(256)
);


ALTER TABLE public."PARTITION_EVENTS" OWNER TO hive;

--
-- Name: PARTITION_KEYS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."PARTITION_KEYS" (
    "TBL_ID" bigint NOT NULL,
    "PKEY_COMMENT" character varying(4000) DEFAULT NULL::character varying,
    "PKEY_NAME" character varying(128) NOT NULL,
    "PKEY_TYPE" character varying(767) NOT NULL,
    "INTEGER_IDX" bigint NOT NULL
);


ALTER TABLE public."PARTITION_KEYS" OWNER TO hive;

--
-- Name: PARTITION_KEY_VALS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."PARTITION_KEY_VALS" (
    "PART_ID" bigint NOT NULL,
    "PART_KEY_VAL" character varying(256) DEFAULT NULL::character varying,
    "INTEGER_IDX" bigint NOT NULL
);


ALTER TABLE public."PARTITION_KEY_VALS" OWNER TO hive;

--
-- Name: PARTITION_PARAMS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."PARTITION_PARAMS" (
    "PART_ID" bigint NOT NULL,
    "PARAM_KEY" character varying(256) NOT NULL,
    "PARAM_VALUE" text
);


ALTER TABLE public."PARTITION_PARAMS" OWNER TO hive;

--
-- Name: PART_COL_PRIVS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."PART_COL_PRIVS" (
    "PART_COLUMN_GRANT_ID" bigint NOT NULL,
    "COLUMN_NAME" character varying(767) DEFAULT NULL::character varying,
    "CREATE_TIME" bigint NOT NULL,
    "GRANT_OPTION" smallint NOT NULL,
    "GRANTOR" character varying(128) DEFAULT NULL::character varying,
    "GRANTOR_TYPE" character varying(128) DEFAULT NULL::character varying,
    "PART_ID" bigint,
    "PRINCIPAL_NAME" character varying(128) DEFAULT NULL::character varying,
    "PRINCIPAL_TYPE" character varying(128) DEFAULT NULL::character varying,
    "PART_COL_PRIV" character varying(128) DEFAULT NULL::character varying,
    "AUTHORIZER" character varying(128) DEFAULT NULL::character varying
);


ALTER TABLE public."PART_COL_PRIVS" OWNER TO hive;

--
-- Name: PART_COL_STATS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."PART_COL_STATS" (
    "CS_ID" bigint NOT NULL,
    "COLUMN_NAME" character varying(767) DEFAULT NULL::character varying,
    "COLUMN_TYPE" character varying(128) DEFAULT NULL::character varying,
    "PART_ID" bigint NOT NULL,
    "LONG_LOW_VALUE" bigint,
    "LONG_HIGH_VALUE" bigint,
    "DOUBLE_LOW_VALUE" double precision,
    "DOUBLE_HIGH_VALUE" double precision,
    "BIG_DECIMAL_LOW_VALUE" character varying(4000) DEFAULT NULL::character varying,
    "BIG_DECIMAL_HIGH_VALUE" character varying(4000) DEFAULT NULL::character varying,
    "NUM_NULLS" bigint NOT NULL,
    "NUM_DISTINCTS" bigint,
    "BIT_VECTOR" bytea,
    "AVG_COL_LEN" double precision,
    "MAX_COL_LEN" bigint,
    "NUM_TRUES" bigint,
    "NUM_FALSES" bigint,
    "LAST_ANALYZED" bigint NOT NULL,
    "ENGINE" character varying(128) NOT NULL,
    "HISTOGRAM" bytea
);


ALTER TABLE public."PART_COL_STATS" OWNER TO hive;

--
-- Name: PART_PRIVS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."PART_PRIVS" (
    "PART_GRANT_ID" bigint NOT NULL,
    "CREATE_TIME" bigint NOT NULL,
    "GRANT_OPTION" smallint NOT NULL,
    "GRANTOR" character varying(128) DEFAULT NULL::character varying,
    "GRANTOR_TYPE" character varying(128) DEFAULT NULL::character varying,
    "PART_ID" bigint,
    "PRINCIPAL_NAME" character varying(128) DEFAULT NULL::character varying,
    "PRINCIPAL_TYPE" character varying(128) DEFAULT NULL::character varying,
    "PART_PRIV" character varying(128) DEFAULT NULL::character varying,
    "AUTHORIZER" character varying(128) DEFAULT NULL::character varying
);


ALTER TABLE public."PART_PRIVS" OWNER TO hive;

--
-- Name: REPLICATION_METRICS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."REPLICATION_METRICS" (
    "RM_SCHEDULED_EXECUTION_ID" bigint NOT NULL,
    "RM_POLICY" character varying(256) NOT NULL,
    "RM_DUMP_EXECUTION_ID" bigint NOT NULL,
    "RM_METADATA" character varying(4000),
    "RM_PROGRESS" character varying(10000),
    "RM_START_TIME" integer NOT NULL,
    "MESSAGE_FORMAT" character varying(16) DEFAULT 'json-0.2'::character varying
);


ALTER TABLE public."REPLICATION_METRICS" OWNER TO hive;

--
-- Name: REPL_TXN_MAP; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."REPL_TXN_MAP" (
    "RTM_REPL_POLICY" character varying(256) NOT NULL,
    "RTM_SRC_TXN_ID" bigint NOT NULL,
    "RTM_TARGET_TXN_ID" bigint NOT NULL
);


ALTER TABLE public."REPL_TXN_MAP" OWNER TO hive;

--
-- Name: ROLES; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."ROLES" (
    "ROLE_ID" bigint NOT NULL,
    "CREATE_TIME" bigint NOT NULL,
    "OWNER_NAME" character varying(128) DEFAULT NULL::character varying,
    "ROLE_NAME" character varying(128) DEFAULT NULL::character varying
);


ALTER TABLE public."ROLES" OWNER TO hive;

--
-- Name: ROLE_MAP; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."ROLE_MAP" (
    "ROLE_GRANT_ID" bigint NOT NULL,
    "ADD_TIME" bigint NOT NULL,
    "GRANT_OPTION" smallint NOT NULL,
    "GRANTOR" character varying(128) DEFAULT NULL::character varying,
    "GRANTOR_TYPE" character varying(128) DEFAULT NULL::character varying,
    "PRINCIPAL_NAME" character varying(128) DEFAULT NULL::character varying,
    "PRINCIPAL_TYPE" character varying(128) DEFAULT NULL::character varying,
    "ROLE_ID" bigint
);


ALTER TABLE public."ROLE_MAP" OWNER TO hive;

--
-- Name: RUNTIME_STATS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."RUNTIME_STATS" (
    "RS_ID" bigint NOT NULL,
    "CREATE_TIME" bigint NOT NULL,
    "WEIGHT" bigint NOT NULL,
    "PAYLOAD" bytea
);


ALTER TABLE public."RUNTIME_STATS" OWNER TO hive;

--
-- Name: SCHEDULED_EXECUTIONS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."SCHEDULED_EXECUTIONS" (
    "SCHEDULED_EXECUTION_ID" bigint NOT NULL,
    "END_TIME" integer,
    "ERROR_MESSAGE" character varying(2000),
    "EXECUTOR_QUERY_ID" character varying(256),
    "LAST_UPDATE_TIME" integer,
    "SCHEDULED_QUERY_ID" bigint,
    "START_TIME" integer,
    "STATE" character varying(256)
);


ALTER TABLE public."SCHEDULED_EXECUTIONS" OWNER TO hive;

--
-- Name: SCHEDULED_QUERIES; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."SCHEDULED_QUERIES" (
    "SCHEDULED_QUERY_ID" bigint NOT NULL,
    "CLUSTER_NAMESPACE" character varying(256),
    "ENABLED" boolean NOT NULL,
    "NEXT_EXECUTION" integer,
    "QUERY" character varying(4000),
    "SCHEDULE" character varying(256),
    "SCHEDULE_NAME" character varying(256),
    "USER" character varying(256),
    "ACTIVE_EXECUTION_ID" bigint
);


ALTER TABLE public."SCHEDULED_QUERIES" OWNER TO hive;

--
-- Name: SCHEMA_VERSION; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."SCHEMA_VERSION" (
    "SCHEMA_VERSION_ID" bigint NOT NULL,
    "SCHEMA_ID" bigint,
    "VERSION" integer NOT NULL,
    "CREATED_AT" bigint NOT NULL,
    "CD_ID" bigint,
    "STATE" integer NOT NULL,
    "DESCRIPTION" character varying(4000),
    "SCHEMA_TEXT" text,
    "FINGERPRINT" character varying(256),
    "SCHEMA_VERSION_NAME" character varying(256),
    "SERDE_ID" bigint
);


ALTER TABLE public."SCHEMA_VERSION" OWNER TO hive;

--
-- Name: SDS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."SDS" (
    "SD_ID" bigint NOT NULL,
    "INPUT_FORMAT" character varying(4000) DEFAULT NULL::character varying,
    "IS_COMPRESSED" boolean NOT NULL,
    "LOCATION" character varying(4000) DEFAULT NULL::character varying,
    "NUM_BUCKETS" bigint NOT NULL,
    "OUTPUT_FORMAT" character varying(4000) DEFAULT NULL::character varying,
    "SERDE_ID" bigint,
    "CD_ID" bigint,
    "IS_STOREDASSUBDIRECTORIES" boolean NOT NULL
);


ALTER TABLE public."SDS" OWNER TO hive;

--
-- Name: SD_PARAMS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."SD_PARAMS" (
    "SD_ID" bigint NOT NULL,
    "PARAM_KEY" character varying(256) NOT NULL,
    "PARAM_VALUE" text
);


ALTER TABLE public."SD_PARAMS" OWNER TO hive;

--
-- Name: SEQUENCE_TABLE; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."SEQUENCE_TABLE" (
    "SEQUENCE_NAME" character varying(255) NOT NULL,
    "NEXT_VAL" bigint NOT NULL
);


ALTER TABLE public."SEQUENCE_TABLE" OWNER TO hive;

--
-- Name: SERDES; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."SERDES" (
    "SERDE_ID" bigint NOT NULL,
    "NAME" character varying(128) DEFAULT NULL::character varying,
    "SLIB" character varying(4000) DEFAULT NULL::character varying,
    "DESCRIPTION" character varying(4000),
    "SERIALIZER_CLASS" character varying(4000),
    "DESERIALIZER_CLASS" character varying(4000),
    "SERDE_TYPE" integer
);


ALTER TABLE public."SERDES" OWNER TO hive;

--
-- Name: SERDE_PARAMS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."SERDE_PARAMS" (
    "SERDE_ID" bigint NOT NULL,
    "PARAM_KEY" character varying(256) NOT NULL,
    "PARAM_VALUE" text
);


ALTER TABLE public."SERDE_PARAMS" OWNER TO hive;

--
-- Name: SKEWED_COL_NAMES; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."SKEWED_COL_NAMES" (
    "SD_ID" bigint NOT NULL,
    "SKEWED_COL_NAME" character varying(256) DEFAULT NULL::character varying,
    "INTEGER_IDX" bigint NOT NULL
);


ALTER TABLE public."SKEWED_COL_NAMES" OWNER TO hive;

--
-- Name: SKEWED_COL_VALUE_LOC_MAP; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."SKEWED_COL_VALUE_LOC_MAP" (
    "SD_ID" bigint NOT NULL,
    "STRING_LIST_ID_KID" bigint NOT NULL,
    "LOCATION" character varying(4000) DEFAULT NULL::character varying
);


ALTER TABLE public."SKEWED_COL_VALUE_LOC_MAP" OWNER TO hive;

--
-- Name: SKEWED_STRING_LIST; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."SKEWED_STRING_LIST" (
    "STRING_LIST_ID" bigint NOT NULL
);


ALTER TABLE public."SKEWED_STRING_LIST" OWNER TO hive;

--
-- Name: SKEWED_STRING_LIST_VALUES; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."SKEWED_STRING_LIST_VALUES" (
    "STRING_LIST_ID" bigint NOT NULL,
    "STRING_LIST_VALUE" character varying(256) DEFAULT NULL::character varying,
    "INTEGER_IDX" bigint NOT NULL
);


ALTER TABLE public."SKEWED_STRING_LIST_VALUES" OWNER TO hive;

--
-- Name: SKEWED_VALUES; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."SKEWED_VALUES" (
    "SD_ID_OID" bigint NOT NULL,
    "STRING_LIST_ID_EID" bigint NOT NULL,
    "INTEGER_IDX" bigint NOT NULL
);


ALTER TABLE public."SKEWED_VALUES" OWNER TO hive;

--
-- Name: SORT_COLS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."SORT_COLS" (
    "SD_ID" bigint NOT NULL,
    "COLUMN_NAME" character varying(767) DEFAULT NULL::character varying,
    "ORDER" bigint NOT NULL,
    "INTEGER_IDX" bigint NOT NULL
);


ALTER TABLE public."SORT_COLS" OWNER TO hive;

--
-- Name: STORED_PROCS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."STORED_PROCS" (
    "SP_ID" bigint NOT NULL,
    "CREATE_TIME" integer NOT NULL,
    "DB_ID" bigint NOT NULL,
    "NAME" character varying(256) NOT NULL,
    "OWNER_NAME" character varying(128) NOT NULL,
    "SOURCE" text NOT NULL
);


ALTER TABLE public."STORED_PROCS" OWNER TO hive;

--
-- Name: TABLE_PARAMS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."TABLE_PARAMS" (
    "TBL_ID" bigint NOT NULL,
    "PARAM_KEY" character varying(256) NOT NULL,
    "PARAM_VALUE" text
);


ALTER TABLE public."TABLE_PARAMS" OWNER TO hive;

--
-- Name: TAB_COL_STATS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."TAB_COL_STATS" (
    "CS_ID" bigint NOT NULL,
    "COLUMN_NAME" character varying(767) DEFAULT NULL::character varying,
    "COLUMN_TYPE" character varying(128) DEFAULT NULL::character varying,
    "TBL_ID" bigint NOT NULL,
    "LONG_LOW_VALUE" bigint,
    "LONG_HIGH_VALUE" bigint,
    "DOUBLE_LOW_VALUE" double precision,
    "DOUBLE_HIGH_VALUE" double precision,
    "BIG_DECIMAL_LOW_VALUE" character varying(4000) DEFAULT NULL::character varying,
    "BIG_DECIMAL_HIGH_VALUE" character varying(4000) DEFAULT NULL::character varying,
    "NUM_NULLS" bigint NOT NULL,
    "NUM_DISTINCTS" bigint,
    "BIT_VECTOR" bytea,
    "AVG_COL_LEN" double precision,
    "MAX_COL_LEN" bigint,
    "NUM_TRUES" bigint,
    "NUM_FALSES" bigint,
    "LAST_ANALYZED" bigint NOT NULL,
    "ENGINE" character varying(128) NOT NULL,
    "HISTOGRAM" bytea
);


ALTER TABLE public."TAB_COL_STATS" OWNER TO hive;

--
-- Name: TBLS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."TBLS" (
    "TBL_ID" bigint NOT NULL,
    "CREATE_TIME" bigint NOT NULL,
    "DB_ID" bigint,
    "LAST_ACCESS_TIME" bigint NOT NULL,
    "OWNER" character varying(767) DEFAULT NULL::character varying,
    "OWNER_TYPE" character varying(10) DEFAULT NULL::character varying,
    "RETENTION" bigint NOT NULL,
    "SD_ID" bigint,
    "TBL_NAME" character varying(256) DEFAULT NULL::character varying,
    "TBL_TYPE" character varying(128) DEFAULT NULL::character varying,
    "VIEW_EXPANDED_TEXT" text,
    "VIEW_ORIGINAL_TEXT" text,
    "IS_REWRITE_ENABLED" boolean DEFAULT false NOT NULL,
    "WRITE_ID" bigint DEFAULT 0
);


ALTER TABLE public."TBLS" OWNER TO hive;

--
-- Name: TBL_COL_PRIVS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."TBL_COL_PRIVS" (
    "TBL_COLUMN_GRANT_ID" bigint NOT NULL,
    "COLUMN_NAME" character varying(767) DEFAULT NULL::character varying,
    "CREATE_TIME" bigint NOT NULL,
    "GRANT_OPTION" smallint NOT NULL,
    "GRANTOR" character varying(128) DEFAULT NULL::character varying,
    "GRANTOR_TYPE" character varying(128) DEFAULT NULL::character varying,
    "PRINCIPAL_NAME" character varying(128) DEFAULT NULL::character varying,
    "PRINCIPAL_TYPE" character varying(128) DEFAULT NULL::character varying,
    "TBL_COL_PRIV" character varying(128) DEFAULT NULL::character varying,
    "TBL_ID" bigint,
    "AUTHORIZER" character varying(128) DEFAULT NULL::character varying
);


ALTER TABLE public."TBL_COL_PRIVS" OWNER TO hive;

--
-- Name: TBL_PRIVS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."TBL_PRIVS" (
    "TBL_GRANT_ID" bigint NOT NULL,
    "CREATE_TIME" bigint NOT NULL,
    "GRANT_OPTION" smallint NOT NULL,
    "GRANTOR" character varying(128) DEFAULT NULL::character varying,
    "GRANTOR_TYPE" character varying(128) DEFAULT NULL::character varying,
    "PRINCIPAL_NAME" character varying(128) DEFAULT NULL::character varying,
    "PRINCIPAL_TYPE" character varying(128) DEFAULT NULL::character varying,
    "TBL_PRIV" character varying(128) DEFAULT NULL::character varying,
    "TBL_ID" bigint,
    "AUTHORIZER" character varying(128) DEFAULT NULL::character varying
);


ALTER TABLE public."TBL_PRIVS" OWNER TO hive;

--
-- Name: TXNS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."TXNS" (
    "TXN_ID" bigint NOT NULL,
    "TXN_STATE" character(1) NOT NULL,
    "TXN_STARTED" bigint NOT NULL,
    "TXN_LAST_HEARTBEAT" bigint NOT NULL,
    "TXN_USER" character varying(128) NOT NULL,
    "TXN_HOST" character varying(128) NOT NULL,
    "TXN_AGENT_INFO" character varying(128),
    "TXN_META_INFO" character varying(128),
    "TXN_HEARTBEAT_COUNT" integer,
    "TXN_TYPE" integer
);


ALTER TABLE public."TXNS" OWNER TO hive;

--
-- Name: TXNS_TXN_ID_seq; Type: SEQUENCE; Schema: public; Owner: hive
--

CREATE SEQUENCE public."TXNS_TXN_ID_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."TXNS_TXN_ID_seq" OWNER TO hive;

--
-- Name: TXNS_TXN_ID_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hive
--

ALTER SEQUENCE public."TXNS_TXN_ID_seq" OWNED BY public."TXNS"."TXN_ID";


--
-- Name: TXN_COMPONENTS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."TXN_COMPONENTS" (
    "TC_TXNID" bigint NOT NULL,
    "TC_DATABASE" character varying(128) NOT NULL,
    "TC_TABLE" character varying(256),
    "TC_PARTITION" character varying(767) DEFAULT NULL::character varying,
    "TC_OPERATION_TYPE" character(1) NOT NULL,
    "TC_WRITEID" bigint
);


ALTER TABLE public."TXN_COMPONENTS" OWNER TO hive;

--
-- Name: TXN_LOCK_TBL; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."TXN_LOCK_TBL" (
    "TXN_LOCK" bigint NOT NULL
);


ALTER TABLE public."TXN_LOCK_TBL" OWNER TO hive;

--
-- Name: TXN_TO_WRITE_ID; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."TXN_TO_WRITE_ID" (
    "T2W_TXNID" bigint NOT NULL,
    "T2W_DATABASE" character varying(128) NOT NULL,
    "T2W_TABLE" character varying(256) NOT NULL,
    "T2W_WRITEID" bigint NOT NULL
);


ALTER TABLE public."TXN_TO_WRITE_ID" OWNER TO hive;

--
-- Name: TXN_WRITE_NOTIFICATION_LOG; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."TXN_WRITE_NOTIFICATION_LOG" (
    "WNL_ID" bigint NOT NULL,
    "WNL_TXNID" bigint NOT NULL,
    "WNL_WRITEID" bigint NOT NULL,
    "WNL_DATABASE" character varying(128) NOT NULL,
    "WNL_TABLE" character varying(256) NOT NULL,
    "WNL_PARTITION" character varying(767) NOT NULL,
    "WNL_TABLE_OBJ" text NOT NULL,
    "WNL_PARTITION_OBJ" text,
    "WNL_FILES" text,
    "WNL_EVENT_TIME" integer NOT NULL
);


ALTER TABLE public."TXN_WRITE_NOTIFICATION_LOG" OWNER TO hive;

--
-- Name: TYPES; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."TYPES" (
    "TYPES_ID" bigint NOT NULL,
    "TYPE_NAME" character varying(128) DEFAULT NULL::character varying,
    "TYPE1" character varying(767) DEFAULT NULL::character varying,
    "TYPE2" character varying(767) DEFAULT NULL::character varying
);


ALTER TABLE public."TYPES" OWNER TO hive;

--
-- Name: TYPE_FIELDS; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."TYPE_FIELDS" (
    "TYPE_NAME" bigint NOT NULL,
    "COMMENT" character varying(256) DEFAULT NULL::character varying,
    "FIELD_NAME" character varying(128) NOT NULL,
    "FIELD_TYPE" character varying(767) NOT NULL,
    "INTEGER_IDX" bigint NOT NULL
);


ALTER TABLE public."TYPE_FIELDS" OWNER TO hive;

--
-- Name: VERSION; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."VERSION" (
    "VER_ID" bigint NOT NULL,
    "SCHEMA_VERSION" character varying(127) NOT NULL,
    "VERSION_COMMENT" character varying(255) NOT NULL
);


ALTER TABLE public."VERSION" OWNER TO hive;

--
-- Name: WM_MAPPING; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."WM_MAPPING" (
    "MAPPING_ID" bigint NOT NULL,
    "RP_ID" bigint NOT NULL,
    "ENTITY_TYPE" character varying(128) NOT NULL,
    "ENTITY_NAME" character varying(128) NOT NULL,
    "POOL_ID" bigint,
    "ORDERING" integer
);


ALTER TABLE public."WM_MAPPING" OWNER TO hive;

--
-- Name: WM_POOL; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."WM_POOL" (
    "POOL_ID" bigint NOT NULL,
    "RP_ID" bigint NOT NULL,
    "PATH" character varying(1024) NOT NULL,
    "ALLOC_FRACTION" double precision,
    "QUERY_PARALLELISM" integer,
    "SCHEDULING_POLICY" character varying(1024)
);


ALTER TABLE public."WM_POOL" OWNER TO hive;

--
-- Name: WM_POOL_TO_TRIGGER; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."WM_POOL_TO_TRIGGER" (
    "POOL_ID" bigint NOT NULL,
    "TRIGGER_ID" bigint NOT NULL
);


ALTER TABLE public."WM_POOL_TO_TRIGGER" OWNER TO hive;

--
-- Name: WM_RESOURCEPLAN; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."WM_RESOURCEPLAN" (
    "RP_ID" bigint NOT NULL,
    "NAME" character varying(128) NOT NULL,
    "NS" character varying(128),
    "QUERY_PARALLELISM" integer,
    "STATUS" character varying(20) NOT NULL,
    "DEFAULT_POOL_ID" bigint
);


ALTER TABLE public."WM_RESOURCEPLAN" OWNER TO hive;

--
-- Name: WM_TRIGGER; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."WM_TRIGGER" (
    "TRIGGER_ID" bigint NOT NULL,
    "RP_ID" bigint NOT NULL,
    "NAME" character varying(128) NOT NULL,
    "TRIGGER_EXPRESSION" character varying(1024) DEFAULT NULL::character varying,
    "ACTION_EXPRESSION" character varying(1024) DEFAULT NULL::character varying,
    "IS_IN_UNMANAGED" smallint DEFAULT 0 NOT NULL
);


ALTER TABLE public."WM_TRIGGER" OWNER TO hive;

--
-- Name: WRITE_SET; Type: TABLE; Schema: public; Owner: hive
--

CREATE TABLE public."WRITE_SET" (
    "WS_DATABASE" character varying(128) NOT NULL,
    "WS_TABLE" character varying(256) NOT NULL,
    "WS_PARTITION" character varying(767),
    "WS_TXNID" bigint NOT NULL,
    "WS_COMMIT_ID" bigint NOT NULL,
    "WS_OPERATION_TYPE" character(1) NOT NULL
);


ALTER TABLE public."WRITE_SET" OWNER TO hive;

--
-- Name: MASTER_KEYS KEY_ID; Type: DEFAULT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."MASTER_KEYS" ALTER COLUMN "KEY_ID" SET DEFAULT nextval('public."MASTER_KEYS_KEY_ID_seq"'::regclass);


--
-- Name: TXNS TXN_ID; Type: DEFAULT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TXNS" ALTER COLUMN "TXN_ID" SET DEFAULT nextval('public."TXNS_TXN_ID_seq"'::regclass);


--
-- Data for Name: AUX_TABLE; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."AUX_TABLE" ("MT_KEY1", "MT_KEY2", "MT_COMMENT") FROM stdin;
Initiator	1791188018413	\N
\.


--
-- Data for Name: BUCKETING_COLS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."BUCKETING_COLS" ("SD_ID", "BUCKET_COL_NAME", "INTEGER_IDX") FROM stdin;
\.


--
-- Data for Name: CATALOG_PARAMS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."CATALOG_PARAMS" ("CTLG_ID", "PARAM_KEY", "PARAM_VALUE") FROM stdin;
\.


--
-- Data for Name: CDS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."CDS" ("CD_ID") FROM stdin;
3
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
71
72
73
74
75
76
77
78
81
\.


--
-- Data for Name: COLUMNS_V2; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."COLUMNS_V2" ("CD_ID", "COMMENT", "COLUMN_NAME", "TYPE_NAME", "INTEGER_IDX") FROM stdin;
3	\N	id_mahasiswa	string	0
3	\N	ipk_kategori	bigint	1
3	\N	selisih_sks	bigint	2
3	\N	jk_enc	bigint	3
3	\N	kecepatan_sks_per_semester	double	4
3	\N	prob_tepat_waktu	double	5
3	\N	prob_terlambat	double	6
3	\N	prediksi	bigint	7
11	\N	id_mahasiswa	string	0
11	\N	ip	double	1
11	\N	sks	int	2
11	\N	jumlah_data_khs	bigint	3
12	\N	nama_kelas	string	0
12	\N	nama_mk	string	1
12	\N	kuota	double	2
13	\N	nama_kelas	string	0
13	\N	nama_mk	string	1
13	\N	kuota	bigint	2
14	\N	id_khs	string	0
14	\N	id_mhs	string	1
14	\N	ip	string	2
14	\N	sks	bigint	3
15	\N	nama kurikulum	string	0
15	\N	jumlah sks total	double	1
16	\N	nama kurikulum	string	0
16	\N	jumlah sks total	bigint	1
17	\N	kode	string	0
17	\N	nama program studi	string	1
17	\N	jumlah dosen	double	2
18	\N	kode	string	0
18	\N	nama program studi	string	1
18	\N	jumlah dosen	bigint	2
19	\N	id_mhs	string	0
19	\N	jenis kelamin	string	1
19	\N	tanggal masuk	string	2
19	\N	tanggal keluar	string	3
19	\N	ipk	double	4
19	\N	total sks	bigint	5
19	\N	jumlah mk	bigint	6
19	\N	status mahasiswa	string	7
20	\N	id_mahasiswa	string	0
20	\N	jk_enc	int	1
20	\N	angkatan	int	2
20	\N	ip	double	3
20	\N	ipk	double	4
20	\N	total_sks	int	5
20	\N	jumlah_mk	int	6
20	\N	sks_seharusnya	int	7
20	\N	selisih_sks	int	8
20	\N	kecepatan_sks_per_semester	double	9
20	\N	ipk_kategori	int	10
21	\N	id_mahasiswa	string	0
21	\N	jk_enc	int	1
21	\N	angkatan	int	2
21	\N	ip	double	3
21	\N	ipk	double	4
21	\N	total_sks	int	5
21	\N	jumlah_mk	int	6
21	\N	sks_seharusnya	int	7
21	\N	selisih_sks	int	8
22	\N	id_mahasiswa	string	0
22	\N	jk_enc	bigint	1
22	\N	angkatan	bigint	2
22	\N	ip	double	3
22	\N	ipk	double	4
22	\N	total_sks	bigint	5
22	\N	jumlah_mk	bigint	6
22	\N	sks_seharusnya	bigint	7
22	\N	selisih_sks	bigint	8
23	\N	id_mahasiswa	string	0
23	\N	ipk_kategori	int	1
23	\N	selisih_sks	int	2
23	\N	jk_enc	int	3
23	\N	kecepatan_sks_per_semester	double	4
23	\N	prob_tepat_waktu	double	5
23	\N	prob_terlambat	double	6
23	\N	prediksi	int	7
24	\N	id_mahasiswa	string	0
24	\N	prediction_without_smote	bigint	1
24	\N	prediction_with_smote	bigint	2
25	\N	id_mahasiswa	string	0
25	\N	jk_enc	int	1
25	\N	angkatan	int	2
25	\N	ip	double	3
25	\N	ipk	double	4
25	\N	total_sks	int	5
25	\N	jumlah_mk	int	6
25	\N	sks_seharusnya	int	7
25	\N	selisih_sks	int	8
25	\N	kecepatan_sks_per_semester	double	9
25	\N	ipk_kategori	int	10
25	\N	label	int	11
26	\N	id_mahasiswa	string	0
26	\N	jk_enc	int	1
26	\N	angkatan	int	2
26	\N	ip	double	3
26	\N	ipk	double	4
26	\N	total_sks	int	5
26	\N	jumlah_mk	int	6
26	\N	sks_seharusnya	int	7
26	\N	selisih_sks	int	8
26	\N	label	int	9
27	\N	id_mahasiswa	string	0
27	\N	jk_enc	bigint	1
27	\N	angkatan	bigint	2
27	\N	ip	double	3
27	\N	ipk	double	4
27	\N	total_sks	bigint	5
27	\N	jumlah_mk	bigint	6
27	\N	sks_seharusnya	bigint	7
27	\N	selisih_sks	bigint	8
27	\N	label	bigint	9
28	\N	id_mahasiswa	string	0
28	\N	jk_enc	bigint	1
28	\N	angkatan	bigint	2
28	\N	ip	double	3
28	\N	ipk	double	4
28	\N	total_sks	bigint	5
28	\N	jumlah_mk	bigint	6
28	\N	sks_seharusnya	bigint	7
28	\N	selisih_sks	bigint	8
28	\N	label	bigint	9
28	\N	persentase_sks	double	10
28	\N	ip_x_progress	double	11
28	\N	rasio_sks_mk	double	12
28	\N	ip_kategori	bigint	13
28	\N	ipk_kategori	bigint	14
28	\N	angkatan_enc	bigint	15
29	\N	class	string	0
29	\N	precision	double	1
29	\N	recall	double	2
29	\N	f1_score	double	3
29	\N	support	int	4
30	\N	model_name	string	0
30	\N	class	string	1
30	\N	precision	double	2
30	\N	recall	double	3
30	\N	f1_score	double	4
30	\N	support	int	5
31	\N	actual	string	0
31	\N	predicted	string	1
31	\N	count	int	2
32	\N	model_name	string	0
32	\N	actual	string	1
32	\N	predicted	string	2
32	\N	count	int	3
33	\N	id_mahasiswa	string	0
33	\N	jenis_kelamin	string	1
33	\N	tanggal_masuk	date	2
33	\N	tanggal_keluar	date	3
33	\N	ipk	double	4
33	\N	total_sks	int	5
33	\N	jumlah_mk	int	6
33	\N	status_mahasiswa	string	7
33	\N	ip	double	8
33	\N	sks	int	9
33	\N	jumlah_data_khs	bigint	10
33	\N	angkatan	int	11
33	\N	semester	int	12
33	\N	sks_seharusnya	int	13
33	\N	selisih_sks	int	14
33	\N	lama_studi	double	15
33	\N	status_kelulusan	string	16
33	\N	label	int	17
34	\N	id_mahasiswa	string	0
34	\N	jenis_kelamin	string	1
34	\N	tanggal_masuk	date	2
34	\N	tanggal_keluar	date	3
34	\N	ipk	double	4
34	\N	total_sks	int	5
34	\N	jumlah_mk	int	6
34	\N	status_mahasiswa	string	7
34	\N	ip	double	8
34	\N	sks_khs	bigint	9
34	\N	jumlah_data_khs	bigint	10
34	\N	angkatan	int	11
34	\N	semester	int	12
34	\N	sks_seharusnya	int	13
34	\N	selisih_sks	int	14
34	\N	lama_studi	double	15
34	\N	status_kelulusan	string	16
34	\N	label	int	17
35	\N	id_mahasiswa	string	0
35	\N	ip	double	1
35	\N	sks_khs	bigint	2
35	\N	jumlah_data_khs	bigint	3
36	\N	nama_kurikulum	string	0
36	\N	jumlah_sks_total	double	1
38	\N	kode	string	0
38	\N	nama_program_studi	string	1
38	\N	jumlah_dosen	double	2
39	\N	id_mahasiswa	string	0
39	\N	angkatan	int	1
39	\N	angkatan_enc	int	2
39	\N	jk_enc	int	3
39	\N	ipk_kategori	int	4
39	\N	total_sks	int	5
39	\N	jumlah_mk	int	6
39	\N	selisih_sks	int	7
39	\N	kecepatan_sks_per_semester	double	8
39	\N	prob_tepat_waktu	double	9
39	\N	prob_terlambat	double	10
39	\N	prediksi	int	11
39	\N	prediksi_label	string	12
40	\N	id_mahasiswa	string	0
40	\N	angkatan	int	1
40	\N	angkatan_enc	int	2
40	\N	jk_enc	int	3
40	\N	ipk_kategori	int	4
40	\N	total_sks	int	5
40	\N	jumlah_mk	int	6
40	\N	selisih_sks	int	7
40	\N	kecepatan_sks_per_semester	double	8
40	\N	prob_tepat_waktu	double	9
40	\N	prob_terlambat	double	10
40	\N	prediksi	int	11
40	\N	prediksi_label	string	12
41	\N	model	string	0
41	\N	cv_mean_accuracy	double	1
41	\N	cv_std_accuracy	double	2
41	\N	cv_mean_f1	double	3
41	\N	cv_std_f1	double	4
41	\N	test_accuracy	double	5
41	\N	test_precision	double	6
41	\N	test_recall	double	7
41	\N	test_f1	double	8
41	\N	training_samples	int	9
41	\N	test_samples	int	10
41	\N	inference_samples	int	11
41	\N	features_count	int	12
41	\N	pipeline_version	string	13
41	\N	training_date	string	14
42	\N	model_name	string	0
42	\N	model_version	string	1
42	\N	cv_accuracy	double	2
42	\N	cv_accuracy_std	double	3
42	\N	cv_precision	double	4
42	\N	cv_precision_std	double	5
42	\N	cv_recall	double	6
42	\N	cv_recall_std	double	7
42	\N	cv_f1	double	8
42	\N	cv_f1_std	double	9
42	\N	train_size	int	10
42	\N	test_size	int	11
42	\N	n_features	int	12
42	\N	features	string	13
42	\N	smote	string	14
42	\N	created_at	timestamp	15
43	\N	id_mahasiswa	string	0
43	\N	angkatan	int	1
43	\N	prediksi	string	2
43	\N	probability	double	3
44	\N	id_mahasiswa	string	0
44	\N	jk_enc	bigint	1
44	\N	angkatan	bigint	2
44	\N	ip	double	3
44	\N	ipk	double	4
44	\N	total_sks	bigint	5
44	\N	jumlah_mk	bigint	6
44	\N	sks_seharusnya	bigint	7
44	\N	selisih_sks	bigint	8
44	\N	persentase_sks	double	9
44	\N	ip_x_progress	double	10
44	\N	rasio_sks_mk	double	11
44	\N	ip_kategori	bigint	12
44	\N	ipk_kategori	bigint	13
44	\N	angkatan_enc	bigint	14
44	\N	probabilitas_tepat_waktu	double	15
44	\N	probabilitas_terlambat	double	16
44	\N	prediksi	bigint	17
44	\N	prediksi_label	string	18
45	\N	angkatan	int	0
45	\N	total_mahasiswa	int	1
45	\N	prediksi_tepat_waktu	int	2
45	\N	prediksi_terlambat	int	3
45	\N	persentase_tepat_waktu	double	4
45	\N	persentase_terlambat	double	5
46	\N	angkatan	int	0
46	\N	prediksi_tepat_waktu	int	1
46	\N	prediksi_terlambat	int	2
46	\N	total	int	3
47	\N	angkatan	bigint	0
47	\N	total_mahasiswa	bigint	1
47	\N	prediksi_tepat_waktu	bigint	2
47	\N	prediksi_terlambat	bigint	3
47	\N	persentase_tepat_waktu	double	4
47	\N	persentase_terlambat	double	5
48	\N	nama_kelas	string	0
48	\N	nama_mk	string	1
48	\N	kuota	double	2
49	\N	id_khs	string	0
49	\N	id_mahasiswa	string	1
49	\N	ip	double	2
49	\N	sks	int	3
50	\N	id_khs	string	0
50	\N	id_mahasiswa	string	1
50	\N	ip	double	2
50	\N	sks	int	3
51	\N	nama_kurikulum	string	0
51	\N	jumlah_sks_total	double	1
52	\N	id_mahasiswa	string	0
52	\N	jenis_kelamin	string	1
52	\N	tanggal_masuk	date	2
52	\N	tanggal_keluar	date	3
52	\N	ipk	double	4
52	\N	total_sks	int	5
52	\N	jumlah_mk	int	6
52	\N	status_mahasiswa	string	7
53	\N	kode	string	0
53	\N	nama_program_studi	string	1
53	\N	jumlah_dosen	double	2
54	\N	id_mahasiswa	string	0
54	\N	jenis_kelamin	string	1
54	\N	tanggal_masuk	date	2
54	\N	tanggal_keluar	date	3
54	\N	ipk	double	4
54	\N	total_sks	int	5
54	\N	jumlah_mk	int	6
54	\N	status_mahasiswa	string	7
55	\N	id_khs	string	0
55	\N	id_mhs	string	1
55	\N	ip	string	2
55	\N	sks	double	3
56	\N	id_mhs	string	0
56	\N	jenis kelamin	string	1
56	\N	tanggal masuk	string	2
56	\N	tanggal keluar	string	3
56	\N	ipk	double	4
56	\N	total sks	double	5
56	\N	jumlah mk	double	6
56	\N	status mahasiswa	string	7
57	\N	id_mhs	string	0
57	\N	jenis_kelamin	string	1
57	\N	ipk	double	2
57	\N	total_sks	int	3
57	\N	jumlah_mk	int	4
57	\N	angkatan	int	5
57	\N	semester	int	6
57	\N	target_sks_kumulatif	int	7
57	\N	selisih_sks	int	8
57	\N	status_kelulusan	string	9
58	\N	id_mhs	string	0
58	\N	jenis_kelamin	string	1
58	\N	angkatan	bigint	2
58	\N	ip	double	3
58	\N	ipk	double	4
58	\N	total_sks	bigint	5
58	\N	jumlah_mk	bigint	6
58	\N	sks_seharusnya	bigint	7
58	\N	selisih_sks	bigint	8
59	\N	id_mhs	string	0
59	\N	jenis_kelamin	string	1
59	\N	angkatan	bigint	2
59	\N	ip	double	3
59	\N	ipk	double	4
59	\N	total_sks	bigint	5
59	\N	jumlah_mk	bigint	6
59	\N	sks_seharusnya	bigint	7
59	\N	selisih_sks	bigint	8
59	\N	label	string	9
60	\N	id_mhs	string	0
60	\N	jenis_kelamin	string	1
60	\N	tanggal_masuk	date	2
60	\N	tanggal_keluar	date	3
60	\N	ipk	double	4
60	\N	total_sks	int	5
60	\N	jumlah_mk	int	6
60	\N	status_mahasiswa	string	7
60	\N	angkatan	int	8
60	\N	semester	int	9
60	\N	target_sks_kumulatif	int	10
60	\N	selisih_sks	int	11
60	\N	lama_studi	double	12
60	\N	status_kelulusan	string	13
61	\N	id_mahasiswa	string	0
61	\N	jk_enc	int	1
61	\N	angkatan	int	2
61	\N	ip	double	3
61	\N	ipk	double	4
61	\N	total_sks	int	5
61	\N	jumlah_mk	int	6
61	\N	sks_seharusnya	int	7
61	\N	selisih_sks	int	8
61	\N	prediksi_label	bigint	9
61	\N	prediksi	string	10
61	\N	probability_tepat_waktu	double	11
61	\N	probability_terlambat	double	12
61	\N	prediction_timestamp	string	13
61	\N	model_version	string	14
61	\N	model_variant	string	15
62	\N	id_mahasiswa	string	0
62	\N	jk_enc	int	1
62	\N	angkatan	int	2
62	\N	ip	double	3
62	\N	ipk	double	4
62	\N	total_sks	int	5
62	\N	jumlah_mk	int	6
62	\N	sks_seharusnya	int	7
62	\N	selisih_sks	int	8
62	\N	prediksi_label	bigint	9
62	\N	prediksi	string	10
62	\N	probability_tepat_waktu	double	11
62	\N	probability_terlambat	double	12
62	\N	prediction_timestamp	string	13
62	\N	model_version	string	14
62	\N	model_variant	string	15
63	\N	id_mahasiswa	string	0
63	\N	ipk_kategori	int	1
63	\N	selisih_sks	int	2
63	\N	jk_enc	int	3
63	\N	kecepatan_sks_per_semester	double	4
63	\N	prob_tepat_waktu	double	5
63	\N	prob_terlambat	double	6
63	\N	prediksi	int	7
71	\N	jenis_kelamin	string	0
71	\N	tanggal_masuk	date	1
71	\N	tanggal_keluar	date	2
71	\N	ipk	double	3
71	\N	total_sks	int	4
71	\N	jumlah_mk	int	5
71	\N	status_mahasiswa	string	6
71	\N	lama_studi_bulan	bigint	7
71	\N	estimasi_semester	bigint	8
71	\N	persentase_sks	double	9
71	\N	status_kelulusan	string	10
72	\N	id_mahasiswa	string	0
72	\N	ip	double	1
72	\N	sks	bigint	2
72	\N	angkatan	bigint	3
72	\N	jumlah_mk	bigint	4
72	\N	prediksi_status_kelulusan	string	5
72	\N	prediction_timestamp	string	6
72	\N	model_version	string	7
73	\N	id_mahasiswa	string	0
73	\N	angkatan	int	1
73	\N	ip	double	2
73	\N	ipk	double	3
73	\N	total_sks	int	4
73	\N	jumlah_mk	int	5
73	\N	sks_seharusnya	int	6
73	\N	selisih_sks	bigint	7
73	\N	jk_enc	int	8
73	\N	ipk_kategori	bigint	9
73	\N	kecepatan_sks_per_semester	double	10
73	\N	probabilitas_tepat_waktu	double	11
73	\N	probabilitas_terlambat	double	12
73	\N	prediksi	bigint	13
73	\N	prediksi_label	string	14
74	\N	angkatan	int	0
74	\N	total_mahasiswa	bigint	1
74	\N	prediksi_tepat_waktu	bigint	2
74	\N	prediksi_terlambat	bigint	3
74	\N	persentase_tepat_waktu	decimal(24,1)	4
74	\N	persentase_terlambat	decimal(24,1)	5
74	\N	total	bigint	6
75	\N	model	string	0
75	\N	cv_mean_accuracy	double	1
75	\N	cv_std_accuracy	double	2
75	\N	cv_mean_f1	double	3
75	\N	cv_std_f1	double	4
75	\N	test_accuracy	double	5
75	\N	test_precision	double	6
75	\N	test_recall	double	7
75	\N	test_f1	double	8
75	\N	training_samples	int	9
75	\N	test_samples	int	10
75	\N	inference_samples	int	11
75	\N	features_count	int	12
75	\N	pipeline_version	string	13
75	\N	training_date	string	14
76	\N	actual	string	0
76	\N	predicted	string	1
76	\N	count	int	2
77	\N	class	string	0
77	\N	precision	double	1
77	\N	recall	double	2
77	\N	f1_score	double	3
77	\N	support	int	4
78	\N	label	int	0
78	\N	jumlah	int	1
81	\N	angkatan	int	0
81	\N	label	int	1
81	\N	jumlah	int	2
\.


--
-- Data for Name: COMPACTION_METRICS_CACHE; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."COMPACTION_METRICS_CACHE" ("CMC_DATABASE", "CMC_TABLE", "CMC_PARTITION", "CMC_METRIC_TYPE", "CMC_METRIC_VALUE", "CMC_VERSION") FROM stdin;
\.


--
-- Data for Name: COMPACTION_QUEUE; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."COMPACTION_QUEUE" ("CQ_ID", "CQ_DATABASE", "CQ_TABLE", "CQ_PARTITION", "CQ_STATE", "CQ_TYPE", "CQ_TBLPROPERTIES", "CQ_WORKER_ID", "CQ_ENQUEUE_TIME", "CQ_START", "CQ_RUN_AS", "CQ_HIGHEST_WRITE_ID", "CQ_META_INFO", "CQ_HADOOP_JOB_ID", "CQ_ERROR_MESSAGE", "CQ_NEXT_TXN_ID", "CQ_TXN_ID", "CQ_COMMIT_TIME", "CQ_INITIATOR_ID", "CQ_INITIATOR_VERSION", "CQ_WORKER_VERSION", "CQ_CLEANER_START", "CQ_RETRY_RETENTION", "CQ_POOL_NAME", "CQ_NUMBER_OF_BUCKETS", "CQ_ORDER_BY") FROM stdin;
\.


--
-- Data for Name: COMPLETED_COMPACTIONS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."COMPLETED_COMPACTIONS" ("CC_ID", "CC_DATABASE", "CC_TABLE", "CC_PARTITION", "CC_STATE", "CC_TYPE", "CC_TBLPROPERTIES", "CC_WORKER_ID", "CC_ENQUEUE_TIME", "CC_START", "CC_END", "CC_RUN_AS", "CC_HIGHEST_WRITE_ID", "CC_META_INFO", "CC_HADOOP_JOB_ID", "CC_ERROR_MESSAGE", "CC_NEXT_TXN_ID", "CC_TXN_ID", "CC_COMMIT_TIME", "CC_INITIATOR_ID", "CC_INITIATOR_VERSION", "CC_WORKER_VERSION", "CC_POOL_NAME", "CC_NUMBER_OF_BUCKETS", "CC_ORDER_BY") FROM stdin;
\.


--
-- Data for Name: COMPLETED_TXN_COMPONENTS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."COMPLETED_TXN_COMPONENTS" ("CTC_TXNID", "CTC_DATABASE", "CTC_TABLE", "CTC_PARTITION", "CTC_TIMESTAMP", "CTC_WRITEID", "CTC_UPDATE_DELETE") FROM stdin;
\.


--
-- Data for Name: CTLGS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."CTLGS" ("CTLG_ID", "NAME", "DESC", "LOCATION_URI", "CREATE_TIME") FROM stdin;
1	hive	Default catalog for Hive	file:/opt/hive/data/warehouse	\N
\.


--
-- Data for Name: DATABASE_PARAMS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."DATABASE_PARAMS" ("DB_ID", "PARAM_KEY", "PARAM_VALUE") FROM stdin;
31	owner	airflow
32	owner	airflow
33	owner	airflow
34	owner	airflow
\.


--
-- Data for Name: DATACONNECTORS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."DATACONNECTORS" ("NAME", "TYPE", "URL", "COMMENT", "OWNER_NAME", "OWNER_TYPE", "CREATE_TIME") FROM stdin;
\.


--
-- Data for Name: DATACONNECTOR_PARAMS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."DATACONNECTOR_PARAMS" ("NAME", "PARAM_KEY", "PARAM_VALUE") FROM stdin;
\.


--
-- Data for Name: DBS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."DBS" ("DB_ID", "DESC", "DB_LOCATION_URI", "NAME", "OWNER_NAME", "OWNER_TYPE", "CTLG_NAME", "CREATE_TIME", "DB_MANAGED_LOCATION_URI", "TYPE", "DATACONNECTOR_NAME", "REMOTE_DBNAME") FROM stdin;
1	Default Hive database	file:/opt/hive/data/warehouse	default	public	ROLE	hive	1791184203	\N	NATIVE	\N	\N
11	\N	file:/opt/hive/data/warehouse/gold.db	gold	root	USER	hive	1791188273	\N	NATIVE	\N	\N
21	\N	file:/opt/hive/data/warehouse/bronze.db	bronze	restore	USER	hive	1791192757	\N	NATIVE	\N	\N
22	\N	file:/opt/hive/data/warehouse/silver.db	silver	restore	USER	hive	1791192758	\N	NATIVE	\N	\N
23	\N	file:/opt/hive/data/warehouse/feature_store.db	feature_store	restore	USER	hive	1791192758	\N	NATIVE	\N	\N
31	\N	s3a://warehouse/iceberg/qa_bronze.db	qa_bronze	airflow	USER	hive	1792123243	\N	NATIVE	\N	\N
32	\N	s3a://warehouse/iceberg/qa_silver.db	qa_silver	airflow	USER	hive	1792123244	\N	NATIVE	\N	\N
33	\N	s3a://warehouse/iceberg/qa_gold.db	qa_gold	airflow	USER	hive	1792123244	\N	NATIVE	\N	\N
34	\N	s3a://warehouse/iceberg/qa_feature_store.db	qa_feature_store	airflow	USER	hive	1792123244	\N	NATIVE	\N	\N
\.


--
-- Data for Name: DB_PRIVS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."DB_PRIVS" ("DB_GRANT_ID", "CREATE_TIME", "DB_ID", "GRANT_OPTION", "GRANTOR", "GRANTOR_TYPE", "PRINCIPAL_NAME", "PRINCIPAL_TYPE", "DB_PRIV", "AUTHORIZER") FROM stdin;
\.


--
-- Data for Name: DC_PRIVS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."DC_PRIVS" ("DC_GRANT_ID", "CREATE_TIME", "NAME", "GRANT_OPTION", "GRANTOR", "GRANTOR_TYPE", "PRINCIPAL_NAME", "PRINCIPAL_TYPE", "DC_PRIV", "AUTHORIZER") FROM stdin;
\.


--
-- Data for Name: DELEGATION_TOKENS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."DELEGATION_TOKENS" ("TOKEN_IDENT", "TOKEN") FROM stdin;
\.


--
-- Data for Name: FUNCS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."FUNCS" ("FUNC_ID", "CLASS_NAME", "CREATE_TIME", "DB_ID", "FUNC_NAME", "FUNC_TYPE", "OWNER_NAME", "OWNER_TYPE") FROM stdin;
\.


--
-- Data for Name: FUNC_RU; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."FUNC_RU" ("FUNC_ID", "RESOURCE_TYPE", "RESOURCE_URI", "INTEGER_IDX") FROM stdin;
\.


--
-- Data for Name: GLOBAL_PRIVS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."GLOBAL_PRIVS" ("USER_GRANT_ID", "CREATE_TIME", "GRANT_OPTION", "GRANTOR", "GRANTOR_TYPE", "PRINCIPAL_NAME", "PRINCIPAL_TYPE", "USER_PRIV", "AUTHORIZER") FROM stdin;
1	1791184203	1	admin	ROLE	admin	ROLE	All	SQL
\.


--
-- Data for Name: HIVE_LOCKS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."HIVE_LOCKS" ("HL_LOCK_EXT_ID", "HL_LOCK_INT_ID", "HL_TXNID", "HL_DB", "HL_TABLE", "HL_PARTITION", "HL_LOCK_STATE", "HL_LOCK_TYPE", "HL_LAST_HEARTBEAT", "HL_ACQUIRED_AT", "HL_USER", "HL_HOST", "HL_HEARTBEAT_COUNT", "HL_AGENT_INFO", "HL_BLOCKEDBY_EXT_ID", "HL_BLOCKEDBY_INT_ID") FROM stdin;
178	1	0	__metastore_leader_election__	metastore_housekeeping	\N	a	x	1792124361689	1792120076585	hive	de1bc899a512	\N	Unknown	\N	\N
177	1	0	__metastore_leader_election__	metastore_always_tasks	\N	a	x	1792124460320	1792120076552	hive	de1bc899a512	\N	Unknown	\N	\N
\.


--
-- Data for Name: I_SCHEMA; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."I_SCHEMA" ("SCHEMA_ID", "SCHEMA_TYPE", "NAME", "DB_ID", "COMPATIBILITY", "VALIDATION_LEVEL", "CAN_EVOLVE", "SCHEMA_GROUP", "DESCRIPTION") FROM stdin;
\.


--
-- Data for Name: KEY_CONSTRAINTS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."KEY_CONSTRAINTS" ("CHILD_CD_ID", "CHILD_INTEGER_IDX", "CHILD_TBL_ID", "PARENT_CD_ID", "PARENT_INTEGER_IDX", "PARENT_TBL_ID", "POSITION", "CONSTRAINT_NAME", "CONSTRAINT_TYPE", "UPDATE_RULE", "DELETE_RULE", "ENABLE_VALIDATE_RELY", "DEFAULT_VALUE") FROM stdin;
\.


--
-- Data for Name: MASTER_KEYS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."MASTER_KEYS" ("KEY_ID", "MASTER_KEY") FROM stdin;
\.


--
-- Data for Name: MATERIALIZATION_REBUILD_LOCKS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."MATERIALIZATION_REBUILD_LOCKS" ("MRL_TXN_ID", "MRL_DB_NAME", "MRL_TBL_NAME", "MRL_LAST_HEARTBEAT") FROM stdin;
\.


--
-- Data for Name: METASTORE_DB_PROPERTIES; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."METASTORE_DB_PROPERTIES" ("PROPERTY_KEY", "PROPERTY_VALUE", "DESCRIPTION", "PROPERTYCONTENT") FROM stdin;
\.


--
-- Data for Name: MIN_HISTORY_LEVEL; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."MIN_HISTORY_LEVEL" ("MHL_TXNID", "MHL_MIN_OPEN_TXNID") FROM stdin;
\.


--
-- Data for Name: MIN_HISTORY_WRITE_ID; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."MIN_HISTORY_WRITE_ID" ("MH_TXNID", "MH_DATABASE", "MH_TABLE", "MH_WRITEID") FROM stdin;
\.


--
-- Data for Name: MV_CREATION_METADATA; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."MV_CREATION_METADATA" ("MV_CREATION_METADATA_ID", "CAT_NAME", "DB_NAME", "TBL_NAME", "TXN_LIST", "MATERIALIZATION_TIME") FROM stdin;
\.


--
-- Data for Name: MV_TABLES_USED; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."MV_TABLES_USED" ("MV_CREATION_METADATA_ID", "TBL_ID", "INSERTED_COUNT", "UPDATED_COUNT", "DELETED_COUNT") FROM stdin;
\.


--
-- Data for Name: NEXT_COMPACTION_QUEUE_ID; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."NEXT_COMPACTION_QUEUE_ID" ("NCQ_NEXT") FROM stdin;
1
\.


--
-- Data for Name: NEXT_LOCK_ID; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."NEXT_LOCK_ID" ("NL_NEXT") FROM stdin;
179
\.


--
-- Data for Name: NEXT_WRITE_ID; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."NEXT_WRITE_ID" ("NWI_DATABASE", "NWI_TABLE", "NWI_NEXT") FROM stdin;
\.


--
-- Data for Name: NOTIFICATION_LOG; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."NOTIFICATION_LOG" ("NL_ID", "EVENT_ID", "EVENT_TIME", "EVENT_TYPE", "CAT_NAME", "DB_NAME", "TBL_NAME", "MESSAGE", "MESSAGE_FORMAT") FROM stdin;
\.


--
-- Data for Name: NOTIFICATION_SEQUENCE; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."NOTIFICATION_SEQUENCE" ("NNI_ID", "NEXT_EVENT_ID") FROM stdin;
1	1
\.


--
-- Data for Name: NUCLEUS_TABLES; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."NUCLEUS_TABLES" ("CLASS_NAME", "TABLE_NAME", "TYPE", "OWNER", "VERSION", "INTERFACE_NAME") FROM stdin;
\.


--
-- Data for Name: PACKAGES; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."PACKAGES" ("PKG_ID", "CREATE_TIME", "DB_ID", "NAME", "OWNER_NAME", "HEADER", "BODY") FROM stdin;
\.


--
-- Data for Name: PARTITIONS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."PARTITIONS" ("PART_ID", "CREATE_TIME", "LAST_ACCESS_TIME", "PART_NAME", "SD_ID", "TBL_ID", "WRITE_ID") FROM stdin;
\.


--
-- Data for Name: PARTITION_EVENTS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."PARTITION_EVENTS" ("PART_NAME_ID", "CAT_NAME", "DB_NAME", "EVENT_TIME", "EVENT_TYPE", "PARTITION_NAME", "TBL_NAME") FROM stdin;
\.


--
-- Data for Name: PARTITION_KEYS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."PARTITION_KEYS" ("TBL_ID", "PKEY_COMMENT", "PKEY_NAME", "PKEY_TYPE", "INTEGER_IDX") FROM stdin;
\.


--
-- Data for Name: PARTITION_KEY_VALS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."PARTITION_KEY_VALS" ("PART_ID", "PART_KEY_VAL", "INTEGER_IDX") FROM stdin;
\.


--
-- Data for Name: PARTITION_PARAMS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."PARTITION_PARAMS" ("PART_ID", "PARAM_KEY", "PARAM_VALUE") FROM stdin;
\.


--
-- Data for Name: PART_COL_PRIVS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."PART_COL_PRIVS" ("PART_COLUMN_GRANT_ID", "COLUMN_NAME", "CREATE_TIME", "GRANT_OPTION", "GRANTOR", "GRANTOR_TYPE", "PART_ID", "PRINCIPAL_NAME", "PRINCIPAL_TYPE", "PART_COL_PRIV", "AUTHORIZER") FROM stdin;
\.


--
-- Data for Name: PART_COL_STATS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."PART_COL_STATS" ("CS_ID", "COLUMN_NAME", "COLUMN_TYPE", "PART_ID", "LONG_LOW_VALUE", "LONG_HIGH_VALUE", "DOUBLE_LOW_VALUE", "DOUBLE_HIGH_VALUE", "BIG_DECIMAL_LOW_VALUE", "BIG_DECIMAL_HIGH_VALUE", "NUM_NULLS", "NUM_DISTINCTS", "BIT_VECTOR", "AVG_COL_LEN", "MAX_COL_LEN", "NUM_TRUES", "NUM_FALSES", "LAST_ANALYZED", "ENGINE", "HISTOGRAM") FROM stdin;
\.


--
-- Data for Name: PART_PRIVS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."PART_PRIVS" ("PART_GRANT_ID", "CREATE_TIME", "GRANT_OPTION", "GRANTOR", "GRANTOR_TYPE", "PART_ID", "PRINCIPAL_NAME", "PRINCIPAL_TYPE", "PART_PRIV", "AUTHORIZER") FROM stdin;
\.


--
-- Data for Name: REPLICATION_METRICS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."REPLICATION_METRICS" ("RM_SCHEDULED_EXECUTION_ID", "RM_POLICY", "RM_DUMP_EXECUTION_ID", "RM_METADATA", "RM_PROGRESS", "RM_START_TIME", "MESSAGE_FORMAT") FROM stdin;
\.


--
-- Data for Name: REPL_TXN_MAP; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."REPL_TXN_MAP" ("RTM_REPL_POLICY", "RTM_SRC_TXN_ID", "RTM_TARGET_TXN_ID") FROM stdin;
\.


--
-- Data for Name: ROLES; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."ROLES" ("ROLE_ID", "CREATE_TIME", "OWNER_NAME", "ROLE_NAME") FROM stdin;
1	1791184203	admin	admin
2	1791184203	public	public
\.


--
-- Data for Name: ROLE_MAP; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."ROLE_MAP" ("ROLE_GRANT_ID", "ADD_TIME", "GRANT_OPTION", "GRANTOR", "GRANTOR_TYPE", "PRINCIPAL_NAME", "PRINCIPAL_TYPE", "ROLE_ID") FROM stdin;
\.


--
-- Data for Name: RUNTIME_STATS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."RUNTIME_STATS" ("RS_ID", "CREATE_TIME", "WEIGHT", "PAYLOAD") FROM stdin;
\.


--
-- Data for Name: SCHEDULED_EXECUTIONS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."SCHEDULED_EXECUTIONS" ("SCHEDULED_EXECUTION_ID", "END_TIME", "ERROR_MESSAGE", "EXECUTOR_QUERY_ID", "LAST_UPDATE_TIME", "SCHEDULED_QUERY_ID", "START_TIME", "STATE") FROM stdin;
\.


--
-- Data for Name: SCHEDULED_QUERIES; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."SCHEDULED_QUERIES" ("SCHEDULED_QUERY_ID", "CLUSTER_NAMESPACE", "ENABLED", "NEXT_EXECUTION", "QUERY", "SCHEDULE", "SCHEDULE_NAME", "USER", "ACTIVE_EXECUTION_ID") FROM stdin;
\.


--
-- Data for Name: SCHEMA_VERSION; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."SCHEMA_VERSION" ("SCHEMA_VERSION_ID", "SCHEMA_ID", "VERSION", "CREATED_AT", "CD_ID", "STATE", "DESCRIPTION", "SCHEMA_TEXT", "FINGERPRINT", "SCHEMA_VERSION_NAME", "SERDE_ID") FROM stdin;
\.


--
-- Data for Name: SDS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."SDS" ("SD_ID", "INPUT_FORMAT", "IS_COMPRESSED", "LOCATION", "NUM_BUCKETS", "OUTPUT_FORMAT", "SERDE_ID", "CD_ID", "IS_STOREDASSUBDIRECTORIES") FROM stdin;
3	org.apache.hadoop.mapred.FileInputFormat	f	file:/opt/hive/data/warehouse/gold.db/inference_result_model_a_utama-4053d948521f466da3c14112d17a56a0	0	org.apache.hadoop.mapred.FileOutputFormat	3	3	f
11	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold.db/fact_khs	0	org.apache.hadoop.mapred.FileOutputFormat	11	11	f
12	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/bronze.db/data_kelas	0	org.apache.hadoop.mapred.FileOutputFormat	12	12	f
13	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/bronze/data_kelas_fix	0	org.apache.hadoop.mapred.FileOutputFormat	13	13	f
14	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/bronze/data_khs_fix	0	org.apache.hadoop.mapred.FileOutputFormat	14	14	f
15	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/bronze.db/data_kurikulum	0	org.apache.hadoop.mapred.FileOutputFormat	15	15	f
16	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/bronze/data_kurikulum_fix	0	org.apache.hadoop.mapred.FileOutputFormat	16	16	f
17	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/bronze.db/data_program_studi	0	org.apache.hadoop.mapred.FileOutputFormat	17	17	f
18	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/bronze/data_program_studi_fix	0	org.apache.hadoop.mapred.FileOutputFormat	18	18	f
19	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/bronze/data_referensi_mahasiswa_fix	0	org.apache.hadoop.mapred.FileOutputFormat	19	19	f
20	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store.db/inference_dataset	0	org.apache.hadoop.mapred.FileOutputFormat	20	20	f
21	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store/inference_dataset_fix	0	org.apache.hadoop.mapred.FileOutputFormat	21	21	f
22	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store.db/inference_dataset_v2	0	org.apache.hadoop.mapred.FileOutputFormat	22	22	f
23	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store.db/inference_result	0	org.apache.hadoop.mapred.FileOutputFormat	23	23	f
24	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store.db/prediction_comparison	0	org.apache.hadoop.mapred.FileOutputFormat	24	24	f
25	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store.db/training_dataset	0	org.apache.hadoop.mapred.FileOutputFormat	25	25	f
26	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store/training_dataset_fix	0	org.apache.hadoop.mapred.FileOutputFormat	26	26	f
27	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store.db/training_dataset_v2	0	org.apache.hadoop.mapred.FileOutputFormat	27	27	f
28	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store.db/training_dataset_v2_fe	0	org.apache.hadoop.mapred.FileOutputFormat	28	28	f
29	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold.db/classification_report	0	org.apache.hadoop.mapred.FileOutputFormat	29	29	f
30	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold/classification_report_final	0	org.apache.hadoop.mapred.FileOutputFormat	30	30	f
31	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold.db/confusion_matrix	0	org.apache.hadoop.mapred.FileOutputFormat	31	31	f
32	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold/confusion_matrix_final	0	org.apache.hadoop.mapred.FileOutputFormat	32	32	f
33	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold.db/dim_mahasiswa	0	org.apache.hadoop.mapred.FileOutputFormat	33	33	f
34	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold/dim_mahasiswa_fix	0	org.apache.hadoop.mapred.FileOutputFormat	34	34	f
35	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold/fact_khs_fix	0	org.apache.hadoop.mapred.FileOutputFormat	35	35	f
36	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold.db/gold_kurikulum	0	org.apache.hadoop.mapred.FileOutputFormat	36	36	f
37	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold/gold_mahasiswa_lama	0	org.apache.hadoop.mapred.FileOutputFormat	37	37	f
38	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold.db/gold_program_studi	0	org.apache.hadoop.mapred.FileOutputFormat	38	38	f
39	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold.db/inference_result_model_utama	0	org.apache.hadoop.mapred.FileOutputFormat	39	39	f
40	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold.db/inference_result_model_utama-d7664e4b37b94b3c99788f1b8604546f	0	org.apache.hadoop.mapred.FileOutputFormat	40	40	f
41	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold.db/model_metrics	0	org.apache.hadoop.mapred.FileOutputFormat	41	41	f
42	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold/model_metrics_final	0	org.apache.hadoop.mapred.FileOutputFormat	42	42	f
43	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold/model_predictions	0	org.apache.hadoop.mapred.FileOutputFormat	43	43	f
44	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold.db/model_predictions_v2	0	org.apache.hadoop.mapred.FileOutputFormat	44	44	f
45	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold.db/prediction_by_angkatan	0	org.apache.hadoop.mapred.FileOutputFormat	45	45	f
46	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold/prediction_by_angkatan_final	0	org.apache.hadoop.mapred.FileOutputFormat	46	46	f
47	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold.db/prediction_by_angkatan_v2	0	org.apache.hadoop.mapred.FileOutputFormat	47	47	f
48	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/silver.db/silver_kelas	0	org.apache.hadoop.mapred.FileOutputFormat	48	48	f
49	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/silver.db/silver_khs	0	org.apache.hadoop.mapred.FileOutputFormat	49	49	f
50	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/silver/silver_khs_fix	0	org.apache.hadoop.mapred.FileOutputFormat	50	50	f
51	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/silver.db/silver_kurikulum	0	org.apache.hadoop.mapred.FileOutputFormat	51	51	f
52	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/silver.db/silver_mahasiswa	0	org.apache.hadoop.mapred.FileOutputFormat	52	52	f
53	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/silver.db/silver_program_studi	0	org.apache.hadoop.mapred.FileOutputFormat	53	53	f
54	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/silver/silver_referensi_mahasiswa_fix	0	org.apache.hadoop.mapred.FileOutputFormat	54	54	f
55	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/bronze.db/data_khs	0	org.apache.hadoop.mapred.FileOutputFormat	55	55	f
56	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/bronze.db/data_referensi_mahasiswa	0	org.apache.hadoop.mapred.FileOutputFormat	56	56	f
57	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store.db/feature_store_graduation_prediction	0	org.apache.hadoop.mapred.FileOutputFormat	57	57	f
58	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store.db/inference_mahasiswa_aktif	0	org.apache.hadoop.mapred.FileOutputFormat	58	58	f
59	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store.db/training_kelulusan	0	org.apache.hadoop.mapred.FileOutputFormat	59	59	f
60	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold.db/data_referensi_mahasiswa	0	org.apache.hadoop.mapred.FileOutputFormat	60	60	f
61	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store.db/prediction_result_with_smote	0	org.apache.hadoop.mapred.FileOutputFormat	61	61	f
62	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store.db/prediction_result_without_smote	0	org.apache.hadoop.mapred.FileOutputFormat	62	62	f
63	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store.db/inference_result	0	org.apache.hadoop.mapred.FileOutputFormat	63	63	f
71	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/gold/gold_mahasiswa	0	org.apache.hadoop.mapred.FileOutputFormat	71	71	f
72	org.apache.hadoop.mapred.FileInputFormat	f	s3a://warehouse/iceberg/feature_store/prediction_result	0	org.apache.hadoop.mapred.FileOutputFormat	72	72	f
73	org.apache.hadoop.mapred.FileInputFormat	f	file:/opt/hive/data/warehouse/gold.db/model_predictions_model_a-80cd10b2d8024076b403f2a74b34f261	0	org.apache.hadoop.mapred.FileOutputFormat	73	73	f
74	org.apache.hadoop.mapred.FileInputFormat	f	file:/opt/hive/data/warehouse/gold.db/prediction_by_angkatan_model_a-719d90c3c5994424a80742099886a80f	0	org.apache.hadoop.mapred.FileOutputFormat	74	74	f
75	org.apache.hadoop.mapred.FileInputFormat	f	file:/opt/hive/data/warehouse/gold.db/model_metrics_model_a-232cda5c32ca4bdcba84017d56bac4c3	0	org.apache.hadoop.mapred.FileOutputFormat	75	75	f
76	org.apache.hadoop.mapred.FileInputFormat	f	file:/opt/hive/data/warehouse/gold.db/confusion_matrix_model_a-552335b47ce648aa9fb654bec7dbb2a2	0	org.apache.hadoop.mapred.FileOutputFormat	76	76	f
77	org.apache.hadoop.mapred.FileInputFormat	f	file:/opt/hive/data/warehouse/gold.db/classification_report_model_a-6ddbcb5b8f5f4c1aae6f12a2a8218222	0	org.apache.hadoop.mapred.FileOutputFormat	77	77	f
78	org.apache.hadoop.mapred.FileInputFormat	f	file:/opt/hive/data/warehouse/gold.db/training_label_distribution_model_a-b935bb3fa2244f548a7916454927eea4	0	org.apache.hadoop.mapred.FileOutputFormat	78	78	f
81	org.apache.hadoop.mapred.FileInputFormat	f	file:/opt/hive/data/warehouse/gold.db/training_label_distribution_by_angkatan-6f6a046a8d4b4f78a748eebcf1941cfc	0	org.apache.hadoop.mapred.FileOutputFormat	81	81	f
\.


--
-- Data for Name: SD_PARAMS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."SD_PARAMS" ("SD_ID", "PARAM_KEY", "PARAM_VALUE") FROM stdin;
\.


--
-- Data for Name: SEQUENCE_TABLE; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."SEQUENCE_TABLE" ("SEQUENCE_NAME", "NEXT_VAL") FROM stdin;
org.apache.hadoop.hive.metastore.model.MNotificationLog	1
org.apache.hadoop.hive.metastore.model.MTxnWriteNotificationLog	1
org.apache.hadoop.hive.metastore.model.MRole	11
org.apache.hadoop.hive.metastore.model.MGlobalPrivilege	11
org.apache.hadoop.hive.metastore.model.MTable	91
org.apache.hadoop.hive.metastore.model.MStorageDescriptor	91
org.apache.hadoop.hive.metastore.model.MSerDeInfo	91
org.apache.hadoop.hive.metastore.model.MColumnDescriptor	91
org.apache.hadoop.hive.metastore.model.MTablePrivilege	291
org.apache.hadoop.hive.metastore.model.MDatabase	41
\.


--
-- Data for Name: SERDES; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."SERDES" ("SERDE_ID", "NAME", "SLIB", "DESCRIPTION", "SERIALIZER_CLASS", "DESERIALIZER_CLASS", "SERDE_TYPE") FROM stdin;
3	inference_result_model_a_utama	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
11	fact_khs	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
12	data_kelas	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
13	data_kelas_fix	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
14	data_khs_fix	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
15	data_kurikulum	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
16	data_kurikulum_fix	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
17	data_program_studi	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
18	data_program_studi_fix	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
19	data_referensi_mahasiswa_fix	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
20	inference_dataset	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
21	inference_dataset_fix	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
22	inference_dataset_v2	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
23	inference_result	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
24	prediction_comparison	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
25	training_dataset	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
26	training_dataset_fix	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
27	training_dataset_v2	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
28	training_dataset_v2_fe	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
29	classification_report	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
30	classification_report_final	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
31	confusion_matrix	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
32	confusion_matrix_final	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
33	dim_mahasiswa	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
34	dim_mahasiswa_fix	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
35	fact_khs_fix	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
36	gold_kurikulum	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
37	gold_mahasiswa_lama	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
38	gold_program_studi	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
39	inference_result_model_utama	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
40	inference_result_model_utama-d7664e4b37b94b3c99788f1b8604546f	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
41	model_metrics	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
42	model_metrics_final	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
43	model_predictions	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
44	model_predictions_v2	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
45	prediction_by_angkatan	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
46	prediction_by_angkatan_final	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
47	prediction_by_angkatan_v2	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
48	silver_kelas	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
49	silver_khs	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
50	silver_khs_fix	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
51	silver_kurikulum	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
52	silver_mahasiswa	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
53	silver_program_studi	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
54	silver_referensi_mahasiswa_fix	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
55	data_khs	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
56	data_referensi_mahasiswa	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
57	feature_store_graduation_prediction	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
58	inference_mahasiswa_aktif	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
59	training_kelulusan	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
60	data_referensi_mahasiswa	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
61	prediction_result_with_smote	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
62	prediction_result_without_smote	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
63	inference_result_new	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
71	gold_mahasiswa	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
72	prediction_result	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
73	model_predictions_model_a	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
74	prediction_by_angkatan_model_a	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
75	model_metrics_model_a	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
76	confusion_matrix_model_a	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
77	classification_report_model_a	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
78	training_label_distribution_model_a	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
81	training_label_distribution_by_angkatan	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	\N	\N	\N	0
\.


--
-- Data for Name: SERDE_PARAMS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."SERDE_PARAMS" ("SERDE_ID", "PARAM_KEY", "PARAM_VALUE") FROM stdin;
\.


--
-- Data for Name: SKEWED_COL_NAMES; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."SKEWED_COL_NAMES" ("SD_ID", "SKEWED_COL_NAME", "INTEGER_IDX") FROM stdin;
\.


--
-- Data for Name: SKEWED_COL_VALUE_LOC_MAP; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."SKEWED_COL_VALUE_LOC_MAP" ("SD_ID", "STRING_LIST_ID_KID", "LOCATION") FROM stdin;
\.


--
-- Data for Name: SKEWED_STRING_LIST; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."SKEWED_STRING_LIST" ("STRING_LIST_ID") FROM stdin;
\.


--
-- Data for Name: SKEWED_STRING_LIST_VALUES; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."SKEWED_STRING_LIST_VALUES" ("STRING_LIST_ID", "STRING_LIST_VALUE", "INTEGER_IDX") FROM stdin;
\.


--
-- Data for Name: SKEWED_VALUES; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."SKEWED_VALUES" ("SD_ID_OID", "STRING_LIST_ID_EID", "INTEGER_IDX") FROM stdin;
\.


--
-- Data for Name: SORT_COLS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."SORT_COLS" ("SD_ID", "COLUMN_NAME", "ORDER", "INTEGER_IDX") FROM stdin;
\.


--
-- Data for Name: STORED_PROCS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."STORED_PROCS" ("SP_ID", "CREATE_TIME", "DB_ID", "NAME", "OWNER_NAME", "SOURCE") FROM stdin;
\.


--
-- Data for Name: TABLE_PARAMS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."TABLE_PARAMS" ("TBL_ID", "PARAM_KEY", "PARAM_VALUE") FROM stdin;
3	table_type	ICEBERG
3	transient_lastDdlTime	1791189664
3	EXTERNAL	TRUE
3	previous_metadata_location	file:/opt/hive/data/warehouse/gold.db/inference_result_model_a_utama-4053d948521f466da3c14112d17a56a0/metadata/00049-0d111a4e-b344-43fd-a42f-4eb2e267723f.metadata.json
3	metadata_location	file:/opt/hive/data/warehouse/gold.db/inference_result_model_a_utama-4053d948521f466da3c14112d17a56a0/metadata/00050-766c2e10-69b9-4062-b03f-5af775eb8c86.metadata.json
11	metadata_location	s3://warehouse/iceberg/gold.db/fact_khs/metadata/00005-29c49e8c-a4df-49c6-ab63-4c593e861ce6.metadata.json
11	transient_lastDdlTime	1791192563
11	numFiles	24
11	trino_query_id	20261005_092922_00139_3ndut
11	table_type	ICEBERG
11	EXTERNAL	TRUE
11	numFilesErasureCoded	0
11	totalSize	896984
12	numFiles	4
12	transient_lastDdlTime	1791192758
12	table_type	ICEBERG
12	metadata_location	s3://warehouse/iceberg/bronze.db/data_kelas/metadata/00000-e5e8859f-e8ae-41e0-a430-933678e3bee8.metadata.json
12	totalSize	34944
12	EXTERNAL	TRUE
12	numFilesErasureCoded	0
12	trino_query_id	20261005_093239_00149_3ndut
13	totalSize	34930
13	metadata_location	s3://warehouse/iceberg/bronze/data_kelas_fix/metadata/v1.metadata.json
13	numFiles	5
13	transient_lastDdlTime	1791192758
13	table_type	ICEBERG
13	trino_query_id	20261005_093239_00150_3ndut
13	EXTERNAL	TRUE
13	numFilesErasureCoded	0
14	trino_query_id	20261005_093239_00152_3ndut
14	numFiles	5
14	transient_lastDdlTime	1791192758
14	table_type	ICEBERG
14	totalSize	231402
14	EXTERNAL	TRUE
14	metadata_location	s3://warehouse/iceberg/bronze/data_khs_fix/metadata/v1.metadata.json
14	numFilesErasureCoded	0
15	numFiles	4
15	trino_query_id	20261005_093239_00153_3ndut
15	totalSize	14452
15	transient_lastDdlTime	1791192758
15	table_type	ICEBERG
15	EXTERNAL	TRUE
15	numFilesErasureCoded	0
15	metadata_location	s3://warehouse/iceberg/bronze.db/data_kurikulum/metadata/00000-e8684509-a829-4969-af34-835d76b5608b.metadata.json
16	numFiles	5
16	metadata_location	s3://warehouse/iceberg/bronze/data_kurikulum_fix/metadata/v1.metadata.json
16	transient_lastDdlTime	1791192758
16	table_type	ICEBERG
16	totalSize	14423
16	trino_query_id	20261005_093239_00154_3ndut
16	EXTERNAL	TRUE
16	numFilesErasureCoded	0
17	trino_query_id	20261005_093239_00155_3ndut
17	numFiles	4
17	totalSize	15049
17	metadata_location	s3://warehouse/iceberg/bronze.db/data_program_studi/metadata/00000-50192666-f131-45d1-b0e8-062b9a415bf3.metadata.json
17	transient_lastDdlTime	1791192758
17	table_type	ICEBERG
17	EXTERNAL	TRUE
17	numFilesErasureCoded	0
18	numFiles	5
18	trino_query_id	20261005_093239_00156_3ndut
18	transient_lastDdlTime	1791192759
18	metadata_location	s3://warehouse/iceberg/bronze/data_program_studi_fix/metadata/v1.metadata.json
18	totalSize	14930
18	table_type	ICEBERG
18	EXTERNAL	TRUE
18	numFilesErasureCoded	0
19	numFiles	5
19	trino_query_id	20261005_093239_00158_3ndut
19	transient_lastDdlTime	1791192759
19	table_type	ICEBERG
19	EXTERNAL	TRUE
19	numFilesErasureCoded	0
19	totalSize	165134
19	metadata_location	s3://warehouse/iceberg/bronze/data_referensi_mahasiswa_fix/metadata/v1.metadata.json
20	totalSize	1259351
20	metadata_location	s3://warehouse/iceberg/feature_store.db/inference_dataset/metadata/00009-6932520a-bd1c-4438-9729-24dbcd5c9f43.metadata.json
20	transient_lastDdlTime	1791192759
20	table_type	ICEBERG
20	numFiles	40
20	EXTERNAL	TRUE
20	numFilesErasureCoded	0
20	trino_query_id	20261005_093239_00160_3ndut
21	numFiles	17
21	trino_query_id	20261005_093240_00161_3ndut
21	transient_lastDdlTime	1791192759
21	totalSize	476911
21	table_type	ICEBERG
21	EXTERNAL	TRUE
21	numFilesErasureCoded	0
21	metadata_location	s3://warehouse/iceberg/feature_store/inference_dataset_fix/metadata/v4.metadata.json
22	trino_query_id	20261005_093240_00162_3ndut
22	totalSize	236732
22	transient_lastDdlTime	1791192759
22	table_type	ICEBERG
22	metadata_location	s3://warehouse/iceberg/feature_store.db/inference_dataset_v2/metadata/00001-35d63533-5e2f-4ea7-bfaa-1fe48c7337f7.metadata.json
22	EXTERNAL	TRUE
22	numFilesErasureCoded	0
22	numFiles	8
23	numFiles	126
23	trino_query_id	20261005_093240_00164_3ndut
23	transient_lastDdlTime	1791192759
23	totalSize	964553
23	table_type	ICEBERG
23	EXTERNAL	TRUE
23	metadata_location	s3://warehouse/iceberg/feature_store.db/inference_result/metadata/00025-1d10989a-94d5-48ea-bad2-8d48c363e291.metadata.json
23	numFilesErasureCoded	0
24	trino_query_id	20261005_093240_00166_3ndut
24	totalSize	5100333
24	metadata_location	s3://warehouse/iceberg/feature_store.db/prediction_comparison/metadata/00062-acaf26a7-dc15-4149-a4fc-c3b834d0ea0b.metadata.json
24	transient_lastDdlTime	1791192759
24	table_type	ICEBERG
24	EXTERNAL	TRUE
24	numFilesErasureCoded	0
24	numFiles	548
25	trino_query_id	20261005_093240_00169_3ndut
25	transient_lastDdlTime	1791192759
25	table_type	ICEBERG
25	numFiles	40
25	EXTERNAL	TRUE
25	numFilesErasureCoded	0
25	metadata_location	s3://warehouse/iceberg/feature_store.db/training_dataset/metadata/00009-ea1fbb28-2fa8-414d-b6ec-7b60713e3251.metadata.json
25	totalSize	1454075
26	numFiles	17
26	totalSize	550223
26	metadata_location	s3://warehouse/iceberg/feature_store/training_dataset_fix/metadata/v4.metadata.json
26	trino_query_id	20261005_093240_00170_3ndut
26	transient_lastDdlTime	1791192759
26	table_type	ICEBERG
26	EXTERNAL	TRUE
26	numFilesErasureCoded	0
27	totalSize	274178
27	metadata_location	s3://warehouse/iceberg/feature_store.db/training_dataset_v2/metadata/00001-a56752ca-a2be-4b5c-8e78-d5d8605edb87.metadata.json
27	transient_lastDdlTime	1791192759
27	table_type	ICEBERG
27	EXTERNAL	TRUE
27	numFilesErasureCoded	0
27	trino_query_id	20261005_093240_00171_3ndut
27	numFiles	8
28	trino_query_id	20261005_093240_00172_3ndut
28	totalSize	188690
28	numFiles	4
28	metadata_location	s3://warehouse/iceberg/feature_store.db/training_dataset_v2_fe/metadata/00000-2f6341cd-22df-4b40-b394-59a734145275.metadata.json
28	transient_lastDdlTime	1791192759
28	table_type	ICEBERG
28	EXTERNAL	TRUE
28	numFilesErasureCoded	0
29	numFiles	6
29	transient_lastDdlTime	1791192760
29	totalSize	18055
29	trino_query_id	20261005_093240_00174_3ndut
29	table_type	ICEBERG
29	EXTERNAL	TRUE
29	numFilesErasureCoded	0
29	metadata_location	s3://warehouse/iceberg/gold.db/classification_report/metadata/00000-e5fc0bef-3b29-4fe2-888d-57f5aa086272.metadata.json
30	numFiles	7
30	transient_lastDdlTime	1791192760
30	trino_query_id	20261005_093240_00175_3ndut
30	totalSize	19374
30	table_type	ICEBERG
30	metadata_location	s3://warehouse/iceberg/gold/classification_report_final/metadata/v2.metadata.json
30	EXTERNAL	TRUE
30	numFilesErasureCoded	0
31	numFiles	7
31	transient_lastDdlTime	1791192760
31	totalSize	17089
31	metadata_location	s3://warehouse/iceberg/gold.db/confusion_matrix/metadata/00000-c8951560-67b6-48b1-9f7a-82b088d59286.metadata.json
31	table_type	ICEBERG
31	trino_query_id	20261005_093240_00176_3ndut
31	EXTERNAL	TRUE
31	numFilesErasureCoded	0
32	numFiles	7
32	transient_lastDdlTime	1791192760
32	totalSize	17793
32	trino_query_id	20261005_093240_00177_3ndut
32	table_type	ICEBERG
32	metadata_location	s3://warehouse/iceberg/gold/confusion_matrix_final/metadata/v2.metadata.json
32	EXTERNAL	TRUE
32	numFilesErasureCoded	0
33	numFiles	28
33	transient_lastDdlTime	1791192760
33	trino_query_id	20261005_093241_00179_3ndut
33	table_type	ICEBERG
33	totalSize	2002167
33	EXTERNAL	TRUE
33	numFilesErasureCoded	0
33	metadata_location	s3://warehouse/iceberg/gold.db/dim_mahasiswa/metadata/00006-65f62a8b-973b-4bb6-aef6-fcff4c8aa633.metadata.json
34	numFiles	5
34	transient_lastDdlTime	1791192760
34	metadata_location	s3://warehouse/iceberg/gold/dim_mahasiswa_fix/metadata/v1.metadata.json
34	totalSize	283057
34	table_type	ICEBERG
34	trino_query_id	20261005_093241_00180_3ndut
34	EXTERNAL	TRUE
34	numFilesErasureCoded	0
35	transient_lastDdlTime	1791192760
35	trino_query_id	20261005_093241_00181_3ndut
35	totalSize	295069
35	table_type	ICEBERG
35	metadata_location	s3://warehouse/iceberg/gold/fact_khs_fix/metadata/v2.metadata.json
35	EXTERNAL	TRUE
35	numFilesErasureCoded	0
35	numFiles	9
36	metadata_location	s3://warehouse/iceberg/gold.db/gold_kurikulum/metadata/00000-5a99b60c-3a5f-44a1-9765-0d1a168ae536.metadata.json
36	transient_lastDdlTime	1791192760
36	numFiles	4
36	trino_query_id	20261005_093241_00182_3ndut
36	table_type	ICEBERG
36	totalSize	14412
36	EXTERNAL	TRUE
36	numFilesErasureCoded	0
37	transient_lastDdlTime	1791192760
37	numFiles	1
37	trino_query_id	20261005_093241_00183_3ndut
37	totalSize	845
37	table_type	ICEBERG
37	EXTERNAL	TRUE
37	numFilesErasureCoded	0
37	metadata_location	s3://warehouse/iceberg/gold/gold_mahasiswa_lama/metadata/00000-68bfe015-d7da-40e0-890f-71ed5f128e63.metadata.json
38	transient_lastDdlTime	1791192760
38	numFiles	4
38	trino_query_id	20261005_093241_00184_3ndut
38	table_type	ICEBERG
38	metadata_location	s3://warehouse/iceberg/gold.db/gold_program_studi/metadata/00000-cd27d0dd-b343-4be2-9a29-e03aae75ae4d.metadata.json
38	totalSize	14964
38	EXTERNAL	TRUE
38	numFilesErasureCoded	0
39	metadata_location	s3://warehouse/iceberg/gold.db/inference_result_model_utama/metadata/00000-9b41ef51-424c-4eca-bedc-f45223634eaa.metadata.json
39	transient_lastDdlTime	1791192760
39	totalSize	7479
39	numFiles	2
39	table_type	ICEBERG
39	trino_query_id	20261005_093241_00185_3ndut
39	EXTERNAL	TRUE
39	numFilesErasureCoded	0
40	transient_lastDdlTime	1791192760
40	metadata_location	s3://warehouse/iceberg/gold.db/inference_result_model_utama-d7664e4b37b94b3c99788f1b8604546f/metadata/00000-e228790b-f19b-4e34-aaef-62a90610f3e5.metadata.json
40	totalSize	7545
40	numFiles	2
40	trino_query_id	20261005_093241_00186_3ndut
40	table_type	ICEBERG
40	EXTERNAL	TRUE
40	numFilesErasureCoded	0
41	transient_lastDdlTime	1791192760
41	numFiles	4
41	totalSize	19663
41	metadata_location	s3://warehouse/iceberg/gold.db/model_metrics/metadata/00000-225b87a1-e584-4540-a717-136b2263f0cb.metadata.json
41	table_type	ICEBERG
41	EXTERNAL	TRUE
41	numFilesErasureCoded	0
41	trino_query_id	20261005_093241_00187_3ndut
42	numFiles	7
42	transient_lastDdlTime	1791192760
42	trino_query_id	20261005_093241_00188_3ndut
42	totalSize	28403
42	table_type	ICEBERG
42	EXTERNAL	TRUE
42	metadata_location	s3://warehouse/iceberg/gold/model_metrics_final/metadata/v2.metadata.json
42	numFilesErasureCoded	0
43	totalSize	228147
43	numFiles	27
43	transient_lastDdlTime	1791192760
43	trino_query_id	20261005_093241_00189_3ndut
43	metadata_location	s3://warehouse/iceberg/gold/model_predictions/metadata/v6.metadata.json
43	table_type	ICEBERG
43	EXTERNAL	TRUE
43	numFilesErasureCoded	0
44	metadata_location	s3://warehouse/iceberg/gold.db/model_predictions_v2/metadata/00001-b5c699bb-9657-4bb2-8386-04aa0d6899fb.metadata.json
44	transient_lastDdlTime	1791192760
44	totalSize	689215
44	table_type	ICEBERG
44	trino_query_id	20261005_093241_00190_3ndut
44	EXTERNAL	TRUE
44	numFilesErasureCoded	0
44	numFiles	8
45	transient_lastDdlTime	1791192761
45	trino_query_id	20261005_093241_00191_3ndut
45	metadata_location	s3://warehouse/iceberg/gold.db/prediction_by_angkatan/metadata/00000-7c16f99b-02d7-4d05-b793-931596ec701d.metadata.json
45	totalSize	24841
45	table_type	ICEBERG
45	EXTERNAL	TRUE
45	numFilesErasureCoded	0
45	numFiles	9
46	transient_lastDdlTime	1791192761
46	numFiles	14
46	metadata_location	s3://warehouse/iceberg/gold/prediction_by_angkatan_final/metadata/v4.metadata.json
46	trino_query_id	20261005_093241_00192_3ndut
46	table_type	ICEBERG
46	totalSize	48272
46	EXTERNAL	TRUE
46	numFilesErasureCoded	0
47	transient_lastDdlTime	1791192761
47	totalSize	32567
47	table_type	ICEBERG
47	metadata_location	s3://warehouse/iceberg/gold.db/prediction_by_angkatan_v2/metadata/00001-8af3f952-fd65-4b19-97be-10b8fdbb4592.metadata.json
47	EXTERNAL	TRUE
47	trino_query_id	20261005_093241_00193_3ndut
47	numFilesErasureCoded	0
47	numFiles	8
48	transient_lastDdlTime	1791192761
48	numFiles	4
48	metadata_location	s3://warehouse/iceberg/silver.db/silver_kelas/metadata/00000-02f8a40f-28b4-4b40-bcde-80466c49831f.metadata.json
48	totalSize	34950
48	table_type	ICEBERG
48	EXTERNAL	TRUE
48	trino_query_id	20261005_093242_00194_3ndut
48	numFilesErasureCoded	0
49	transient_lastDdlTime	1791192761
49	metadata_location	s3://warehouse/iceberg/silver.db/silver_khs/metadata/00000-2ffdec16-6762-4a87-9cb6-5ce2166c1dce.metadata.json
49	numFiles	4
49	trino_query_id	20261005_093242_00195_3ndut
49	table_type	ICEBERG
49	EXTERNAL	TRUE
49	numFilesErasureCoded	0
49	totalSize	228537
50	transient_lastDdlTime	1791192761
50	trino_query_id	20261005_093242_00196_3ndut
50	metadata_location	s3://warehouse/iceberg/silver/silver_khs_fix/metadata/v2.metadata.json
50	table_type	ICEBERG
50	totalSize	458044
50	EXTERNAL	TRUE
50	numFilesErasureCoded	0
50	numFiles	9
51	transient_lastDdlTime	1791192761
51	trino_query_id	20261005_093242_00197_3ndut
51	metadata_location	s3://warehouse/iceberg/silver.db/silver_kurikulum/metadata/00000-b4eef25b-3074-4a27-88f6-7efd91a4ccc6.metadata.json
51	numFiles	4
51	table_type	ICEBERG
51	totalSize	14426
51	EXTERNAL	TRUE
51	numFilesErasureCoded	0
52	transient_lastDdlTime	1791192761
52	numFiles	4
52	totalSize	156458
52	metadata_location	s3://warehouse/iceberg/silver.db/silver_mahasiswa/metadata/00000-385fbfd8-7508-4ed2-ad2a-b66f10c9f285.metadata.json
52	trino_query_id	20261005_093242_00198_3ndut
52	table_type	ICEBERG
52	EXTERNAL	TRUE
52	numFilesErasureCoded	0
53	transient_lastDdlTime	1791192761
53	numFiles	4
53	totalSize	14974
53	table_type	ICEBERG
53	metadata_location	s3://warehouse/iceberg/silver.db/silver_program_studi/metadata/00000-0b432eb6-a1f3-4952-8b33-999208a4da42.metadata.json
53	EXTERNAL	TRUE
53	trino_query_id	20261005_093242_00199_3ndut
53	numFilesErasureCoded	0
54	transient_lastDdlTime	1791192761
54	trino_query_id	20261005_093242_00200_3ndut
54	totalSize	313934
54	table_type	ICEBERG
54	metadata_location	s3://warehouse/iceberg/silver/silver_referensi_mahasiswa_fix/metadata/v2.metadata.json
54	EXTERNAL	TRUE
54	numFilesErasureCoded	0
54	numFiles	9
55	trino_query_id	20261005_100349_00254_3ndut
55	transient_lastDdlTime	1791194632
55	numFiles	112
55	totalSize	1341623
55	metadata_location	s3://warehouse/iceberg/bronze.db/data_khs/metadata/00000-38cdeedc-4add-403c-91c7-5f4205a5dd10.metadata.json
55	table_type	ICEBERG
55	EXTERNAL	TRUE
55	numFilesErasureCoded	0
56	transient_lastDdlTime	1791194632
56	totalSize	925733
56	metadata_location	s3://warehouse/iceberg/bronze.db/data_referensi_mahasiswa/metadata/00000-579a25b5-d45c-4b90-b740-92e83b8361ab.metadata.json
56	numFiles	85
56	table_type	ICEBERG
56	EXTERNAL	TRUE
56	numFilesErasureCoded	0
56	trino_query_id	20261005_100349_00255_3ndut
57	metadata_location	s3://warehouse/iceberg/feature_store.db/feature_store_graduation_prediction/metadata/00000-0c483f19-04be-4269-b3be-af0fbac0c0f1.metadata.json
57	transient_lastDdlTime	1791194632
57	totalSize	192702
57	trino_query_id	20261005_100349_00256_3ndut
57	table_type	ICEBERG
57	EXTERNAL	TRUE
57	numFilesErasureCoded	0
57	numFiles	8
58	transient_lastDdlTime	1791194632
58	metadata_location	s3://warehouse/iceberg/feature_store.db/inference_mahasiswa_aktif/metadata/00000-b2cb8d94-fb1a-4593-93d3-48a33fa3ef71.metadata.json
58	totalSize	590081
58	numFiles	58
58	trino_query_id	20261005_100350_00257_3ndut
58	table_type	ICEBERG
58	EXTERNAL	TRUE
58	numFilesErasureCoded	0
59	transient_lastDdlTime	1791194632
59	trino_query_id	20261005_100350_00258_3ndut
59	numFiles	58
59	totalSize	521633
59	metadata_location	s3://warehouse/iceberg/feature_store.db/training_kelulusan/metadata/00000-8f1ab441-a0c3-46af-9bae-4e4817918208.metadata.json
59	table_type	ICEBERG
59	EXTERNAL	TRUE
59	numFilesErasureCoded	0
60	totalSize	867559
60	metadata_location	s3://warehouse/iceberg/gold.db/data_referensi_mahasiswa/metadata/00000-62754705-6b96-49b3-9d70-d46bbe1caae7.metadata.json
60	numFiles	12
60	table_type	ICEBERG
60	trino_query_id	20261005_100350_00259_3ndut
60	EXTERNAL	TRUE
60	numFilesErasureCoded	0
60	transient_lastDdlTime	1791194633
61	totalSize	12408093
61	trino_query_id	20261005_100350_00260_3ndut
61	table_type	ICEBERG
61	metadata_location	s3://warehouse/iceberg/feature_store.db/prediction_result_with_smote/metadata/00063-099d5882-99e8-4425-87b4-4eb0429a1324.metadata.json
61	EXTERNAL	TRUE
61	numFilesErasureCoded	0
61	numFiles	944
61	transient_lastDdlTime	1791194633
62	trino_query_id	20261005_100350_00261_3ndut
62	metadata_location	s3://warehouse/iceberg/feature_store.db/prediction_result_without_smote/metadata/00063-c0ed2509-9c72-4bc9-86cd-5ca6cf2108b8.metadata.json
62	totalSize	16638844
62	table_type	ICEBERG
62	numFiles	1260
62	EXTERNAL	TRUE
62	numFilesErasureCoded	0
62	transient_lastDdlTime	1791194633
63	numFiles	126
63	totalSize	964553
63	table_type	ICEBERG
63	EXTERNAL	TRUE
63	trino_query_id	20261005_100350_00262_3ndut
63	metadata_location	s3://warehouse/iceberg/feature_store.db/inference_result/metadata/00025-1d10989a-94d5-48ea-bad2-8d48c363e291.metadata.json
63	numFilesErasureCoded	0
63	transient_lastDdlTime	1791194633
71	numFiles	6
71	totalSize	180943
71	trino_query_id	20261008_051512_00000_84e7v
71	metadata_location	s3://warehouse/iceberg/gold/gold_mahasiswa/metadata/v1.metadata.json
71	table_type	ICEBERG
71	transient_lastDdlTime	1791436513
71	EXTERNAL	TRUE
71	numFilesErasureCoded	0
72	metadata_location	s3://warehouse/iceberg/feature_store/prediction_result/metadata/v2.metadata.json
72	trino_query_id	20261008_051625_00001_84e7v
72	table_type	ICEBERG
72	transient_lastDdlTime	1791436585
72	EXTERNAL	TRUE
72	numFilesErasureCoded	0
72	numFiles	9
72	totalSize	309336
73	transient_lastDdlTime	1791442603
73	table_type	ICEBERG
73	EXTERNAL	TRUE
73	previous_metadata_location	file:/opt/hive/data/warehouse/gold.db/model_predictions_model_a-80cd10b2d8024076b403f2a74b34f261/metadata/00000-fa2266b8-aec1-4699-aad6-e5e1ef9bbee1.metadata.json
73	metadata_location	file:/opt/hive/data/warehouse/gold.db/model_predictions_model_a-80cd10b2d8024076b403f2a74b34f261/metadata/00001-94dfe4e0-e211-4d4d-9563-b8cba66a74c4.metadata.json
74	table_type	ICEBERG
74	EXTERNAL	TRUE
74	transient_lastDdlTime	1791442621
74	previous_metadata_location	file:/opt/hive/data/warehouse/gold.db/prediction_by_angkatan_model_a-719d90c3c5994424a80742099886a80f/metadata/00000-f23d17fd-a6e0-460e-a07a-e9c8e5074ae6.metadata.json
74	metadata_location	file:/opt/hive/data/warehouse/gold.db/prediction_by_angkatan_model_a-719d90c3c5994424a80742099886a80f/metadata/00001-12cbaa80-e726-4f10-a072-088a13a63d4c.metadata.json
75	transient_lastDdlTime	1791443736
75	table_type	ICEBERG
75	EXTERNAL	TRUE
75	previous_metadata_location	file:/opt/hive/data/warehouse/gold.db/model_metrics_model_a-232cda5c32ca4bdcba84017d56bac4c3/metadata/00001-eebab2e4-5a1c-490c-820d-c436804e8055.metadata.json
75	metadata_location	file:/opt/hive/data/warehouse/gold.db/model_metrics_model_a-232cda5c32ca4bdcba84017d56bac4c3/metadata/00002-f54342a8-6ddd-420e-83a6-77a762b752f4.metadata.json
76	transient_lastDdlTime	1791443737
76	table_type	ICEBERG
76	EXTERNAL	TRUE
76	previous_metadata_location	file:/opt/hive/data/warehouse/gold.db/confusion_matrix_model_a-552335b47ce648aa9fb654bec7dbb2a2/metadata/00001-9445a0dc-0bf8-4be6-8ff3-7d5386ae14e3.metadata.json
76	metadata_location	file:/opt/hive/data/warehouse/gold.db/confusion_matrix_model_a-552335b47ce648aa9fb654bec7dbb2a2/metadata/00002-4d25ab15-4dcc-4281-b45a-ef6622fe5d08.metadata.json
77	transient_lastDdlTime	1791443737
77	table_type	ICEBERG
77	EXTERNAL	TRUE
77	previous_metadata_location	file:/opt/hive/data/warehouse/gold.db/classification_report_model_a-6ddbcb5b8f5f4c1aae6f12a2a8218222/metadata/00001-56f39518-bf55-4d0f-bb4e-951c27260b80.metadata.json
77	metadata_location	file:/opt/hive/data/warehouse/gold.db/classification_report_model_a-6ddbcb5b8f5f4c1aae6f12a2a8218222/metadata/00002-a923e79c-2dd1-40da-b394-dabd784d2e40.metadata.json
78	transient_lastDdlTime	1791444626
78	table_type	ICEBERG
78	EXTERNAL	TRUE
78	previous_metadata_location	file:/opt/hive/data/warehouse/gold.db/training_label_distribution_model_a-b935bb3fa2244f548a7916454927eea4/metadata/00001-0fff874c-7712-4e3b-8c9e-25113a5cc6ae.metadata.json
78	metadata_location	file:/opt/hive/data/warehouse/gold.db/training_label_distribution_model_a-b935bb3fa2244f548a7916454927eea4/metadata/00002-3c54a0d9-a35d-49b0-af8b-6e96e906b5f2.metadata.json
81	transient_lastDdlTime	1792040394
81	table_type	ICEBERG
81	EXTERNAL	TRUE
81	previous_metadata_location	file:/opt/hive/data/warehouse/gold.db/training_label_distribution_by_angkatan-6f6a046a8d4b4f78a748eebcf1941cfc/metadata/00000-ad95074c-f9b2-45b0-9812-66ac11cfc769.metadata.json
81	metadata_location	file:/opt/hive/data/warehouse/gold.db/training_label_distribution_by_angkatan-6f6a046a8d4b4f78a748eebcf1941cfc/metadata/00001-f899dd92-0a20-4dc8-bf7c-e80d33510321.metadata.json
\.


--
-- Data for Name: TAB_COL_STATS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."TAB_COL_STATS" ("CS_ID", "COLUMN_NAME", "COLUMN_TYPE", "TBL_ID", "LONG_LOW_VALUE", "LONG_HIGH_VALUE", "DOUBLE_LOW_VALUE", "DOUBLE_HIGH_VALUE", "BIG_DECIMAL_LOW_VALUE", "BIG_DECIMAL_HIGH_VALUE", "NUM_NULLS", "NUM_DISTINCTS", "BIT_VECTOR", "AVG_COL_LEN", "MAX_COL_LEN", "NUM_TRUES", "NUM_FALSES", "LAST_ANALYZED", "ENGINE", "HISTOGRAM") FROM stdin;
\.


--
-- Data for Name: TBLS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."TBLS" ("TBL_ID", "CREATE_TIME", "DB_ID", "LAST_ACCESS_TIME", "OWNER", "OWNER_TYPE", "RETENTION", "SD_ID", "TBL_NAME", "TBL_TYPE", "VIEW_EXPANDED_TEXT", "VIEW_ORIGINAL_TEXT", "IS_REWRITE_ENABLED", "WRITE_ID") FROM stdin;
3	1791189664	11	0	airflow	USER	0	3	inference_result_model_a_utama	EXTERNAL_TABLE	\N	\N	f	0
11	1791192563	11	0	root	USER	0	11	fact_khs	EXTERNAL_TABLE	\N	\N	f	0
12	1791192758	21	0	restore	USER	0	12	data_kelas	EXTERNAL_TABLE	\N	\N	f	0
13	1791192758	21	0	restore	USER	0	13	data_kelas_fix	EXTERNAL_TABLE	\N	\N	f	0
14	1791192758	21	0	restore	USER	0	14	data_khs_fix	EXTERNAL_TABLE	\N	\N	f	0
15	1791192758	21	0	restore	USER	0	15	data_kurikulum	EXTERNAL_TABLE	\N	\N	f	0
16	1791192758	21	0	restore	USER	0	16	data_kurikulum_fix	EXTERNAL_TABLE	\N	\N	f	0
17	1791192758	21	0	restore	USER	0	17	data_program_studi	EXTERNAL_TABLE	\N	\N	f	0
18	1791192759	21	0	restore	USER	0	18	data_program_studi_fix	EXTERNAL_TABLE	\N	\N	f	0
19	1791192759	21	0	restore	USER	0	19	data_referensi_mahasiswa_fix	EXTERNAL_TABLE	\N	\N	f	0
20	1791192759	23	0	restore	USER	0	20	inference_dataset	EXTERNAL_TABLE	\N	\N	f	0
21	1791192759	23	0	restore	USER	0	21	inference_dataset_fix	EXTERNAL_TABLE	\N	\N	f	0
22	1791192759	23	0	restore	USER	0	22	inference_dataset_v2	EXTERNAL_TABLE	\N	\N	f	0
23	1791192759	23	0	restore	USER	0	23	inference_result	EXTERNAL_TABLE	\N	\N	f	0
24	1791192759	23	0	restore	USER	0	24	prediction_comparison	EXTERNAL_TABLE	\N	\N	f	0
25	1791192759	23	0	restore	USER	0	25	training_dataset	EXTERNAL_TABLE	\N	\N	f	0
26	1791192759	23	0	restore	USER	0	26	training_dataset_fix	EXTERNAL_TABLE	\N	\N	f	0
27	1791192759	23	0	restore	USER	0	27	training_dataset_v2	EXTERNAL_TABLE	\N	\N	f	0
28	1791192759	23	0	restore	USER	0	28	training_dataset_v2_fe	EXTERNAL_TABLE	\N	\N	f	0
29	1791192760	11	0	restore	USER	0	29	classification_report	EXTERNAL_TABLE	\N	\N	f	0
30	1791192760	11	0	restore	USER	0	30	classification_report_final	EXTERNAL_TABLE	\N	\N	f	0
31	1791192760	11	0	restore	USER	0	31	confusion_matrix	EXTERNAL_TABLE	\N	\N	f	0
32	1791192760	11	0	restore	USER	0	32	confusion_matrix_final	EXTERNAL_TABLE	\N	\N	f	0
33	1791192760	11	0	restore	USER	0	33	dim_mahasiswa	EXTERNAL_TABLE	\N	\N	f	0
34	1791192760	11	0	restore	USER	0	34	dim_mahasiswa_fix	EXTERNAL_TABLE	\N	\N	f	0
35	1791192760	11	0	restore	USER	0	35	fact_khs_fix	EXTERNAL_TABLE	\N	\N	f	0
36	1791192760	11	0	restore	USER	0	36	gold_kurikulum	EXTERNAL_TABLE	\N	\N	f	0
37	1791192760	11	0	restore	USER	0	37	gold_mahasiswa_lama	EXTERNAL_TABLE	\N	\N	f	0
38	1791192760	11	0	restore	USER	0	38	gold_program_studi	EXTERNAL_TABLE	\N	\N	f	0
39	1791192760	11	0	restore	USER	0	39	inference_result_model_utama	EXTERNAL_TABLE	\N	\N	f	0
40	1791192760	11	0	restore	USER	0	40	inference_result_model_utama-d7664e4b37b94b3c99788f1b8604546f	EXTERNAL_TABLE	\N	\N	f	0
41	1791192760	11	0	restore	USER	0	41	model_metrics	EXTERNAL_TABLE	\N	\N	f	0
42	1791192760	11	0	restore	USER	0	42	model_metrics_final	EXTERNAL_TABLE	\N	\N	f	0
43	1791192760	11	0	restore	USER	0	43	model_predictions	EXTERNAL_TABLE	\N	\N	f	0
44	1791192760	11	0	restore	USER	0	44	model_predictions_v2	EXTERNAL_TABLE	\N	\N	f	0
45	1791192761	11	0	restore	USER	0	45	prediction_by_angkatan	EXTERNAL_TABLE	\N	\N	f	0
46	1791192761	11	0	restore	USER	0	46	prediction_by_angkatan_final	EXTERNAL_TABLE	\N	\N	f	0
47	1791192761	11	0	restore	USER	0	47	prediction_by_angkatan_v2	EXTERNAL_TABLE	\N	\N	f	0
48	1791192761	22	0	restore	USER	0	48	silver_kelas	EXTERNAL_TABLE	\N	\N	f	0
49	1791192761	22	0	restore	USER	0	49	silver_khs	EXTERNAL_TABLE	\N	\N	f	0
50	1791192761	22	0	restore	USER	0	50	silver_khs_fix	EXTERNAL_TABLE	\N	\N	f	0
51	1791192761	22	0	restore	USER	0	51	silver_kurikulum	EXTERNAL_TABLE	\N	\N	f	0
52	1791192761	22	0	restore	USER	0	52	silver_mahasiswa	EXTERNAL_TABLE	\N	\N	f	0
53	1791192761	22	0	restore	USER	0	53	silver_program_studi	EXTERNAL_TABLE	\N	\N	f	0
54	1791192761	22	0	restore	USER	0	54	silver_referensi_mahasiswa_fix	EXTERNAL_TABLE	\N	\N	f	0
55	1791194632	21	0	restore	USER	0	55	data_khs	EXTERNAL_TABLE	\N	\N	f	0
56	1791194632	21	0	restore	USER	0	56	data_referensi_mahasiswa	EXTERNAL_TABLE	\N	\N	f	0
57	1791194632	23	0	restore	USER	0	57	feature_store_graduation_prediction	EXTERNAL_TABLE	\N	\N	f	0
58	1791194632	23	0	restore	USER	0	58	inference_mahasiswa_aktif	EXTERNAL_TABLE	\N	\N	f	0
59	1791194632	23	0	restore	USER	0	59	training_kelulusan	EXTERNAL_TABLE	\N	\N	f	0
60	1791194633	11	0	restore	USER	0	60	data_referensi_mahasiswa	EXTERNAL_TABLE	\N	\N	f	0
61	1791194633	23	0	restore	USER	0	61	prediction_result_with_smote	EXTERNAL_TABLE	\N	\N	f	0
62	1791194633	23	0	restore	USER	0	62	prediction_result_without_smote	EXTERNAL_TABLE	\N	\N	f	0
63	1791194633	23	0	restore	USER	0	63	inference_result_new	EXTERNAL_TABLE	\N	\N	f	0
71	1791436513	11	0	root	USER	0	71	gold_mahasiswa	EXTERNAL_TABLE	\N	\N	f	0
72	1791436585	23	0	root	USER	0	72	prediction_result	EXTERNAL_TABLE	\N	\N	f	0
73	1791442603	11	0	root	USER	0	73	model_predictions_model_a	EXTERNAL_TABLE	\N	\N	f	0
74	1791442621	11	0	root	USER	0	74	prediction_by_angkatan_model_a	EXTERNAL_TABLE	\N	\N	f	0
75	1791443736	11	0	root	USER	0	75	model_metrics_model_a	EXTERNAL_TABLE	\N	\N	f	0
76	1791443737	11	0	root	USER	0	76	confusion_matrix_model_a	EXTERNAL_TABLE	\N	\N	f	0
77	1791443737	11	0	root	USER	0	77	classification_report_model_a	EXTERNAL_TABLE	\N	\N	f	0
78	1791444626	11	0	root	USER	0	78	training_label_distribution_model_a	EXTERNAL_TABLE	\N	\N	f	0
81	1792040394	11	0	root	USER	0	81	training_label_distribution_by_angkatan	EXTERNAL_TABLE	\N	\N	f	0
\.


--
-- Data for Name: TBL_COL_PRIVS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."TBL_COL_PRIVS" ("TBL_COLUMN_GRANT_ID", "COLUMN_NAME", "CREATE_TIME", "GRANT_OPTION", "GRANTOR", "GRANTOR_TYPE", "PRINCIPAL_NAME", "PRINCIPAL_TYPE", "TBL_COL_PRIV", "TBL_ID", "AUTHORIZER") FROM stdin;
\.


--
-- Data for Name: TBL_PRIVS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."TBL_PRIVS" ("TBL_GRANT_ID", "CREATE_TIME", "GRANT_OPTION", "GRANTOR", "GRANTOR_TYPE", "PRINCIPAL_NAME", "PRINCIPAL_TYPE", "TBL_PRIV", "TBL_ID", "AUTHORIZER") FROM stdin;
9	1791189664	1	airflow	USER	airflow	USER	select	3	SQL
10	1791189664	1	airflow	USER	airflow	USER	insert	3	SQL
11	1791189664	1	airflow	USER	airflow	USER	update	3	SQL
12	1791189664	1	airflow	USER	airflow	USER	delete	3	SQL
21	1791192563	1	root	USER	root	USER	select	11	SQL
22	1791192563	1	root	USER	root	USER	insert	11	SQL
23	1791192563	1	root	USER	root	USER	update	11	SQL
24	1791192563	1	root	USER	root	USER	delete	11	SQL
25	1791192758	1	restore	USER	restore	USER	select	12	SQL
26	1791192758	1	restore	USER	restore	USER	insert	12	SQL
27	1791192758	1	restore	USER	restore	USER	update	12	SQL
28	1791192758	1	restore	USER	restore	USER	delete	12	SQL
29	1791192758	1	restore	USER	restore	USER	select	13	SQL
30	1791192758	1	restore	USER	restore	USER	insert	13	SQL
31	1791192758	1	restore	USER	restore	USER	update	13	SQL
32	1791192758	1	restore	USER	restore	USER	delete	13	SQL
33	1791192758	1	restore	USER	restore	USER	select	14	SQL
34	1791192758	1	restore	USER	restore	USER	insert	14	SQL
35	1791192758	1	restore	USER	restore	USER	update	14	SQL
36	1791192758	1	restore	USER	restore	USER	delete	14	SQL
37	1791192758	1	restore	USER	restore	USER	select	15	SQL
38	1791192758	1	restore	USER	restore	USER	insert	15	SQL
39	1791192758	1	restore	USER	restore	USER	update	15	SQL
40	1791192758	1	restore	USER	restore	USER	delete	15	SQL
41	1791192758	1	restore	USER	restore	USER	select	16	SQL
42	1791192758	1	restore	USER	restore	USER	insert	16	SQL
43	1791192758	1	restore	USER	restore	USER	update	16	SQL
44	1791192758	1	restore	USER	restore	USER	delete	16	SQL
45	1791192758	1	restore	USER	restore	USER	select	17	SQL
46	1791192758	1	restore	USER	restore	USER	insert	17	SQL
47	1791192758	1	restore	USER	restore	USER	update	17	SQL
48	1791192758	1	restore	USER	restore	USER	delete	17	SQL
49	1791192759	1	restore	USER	restore	USER	select	18	SQL
50	1791192759	1	restore	USER	restore	USER	insert	18	SQL
51	1791192759	1	restore	USER	restore	USER	update	18	SQL
52	1791192759	1	restore	USER	restore	USER	delete	18	SQL
53	1791192759	1	restore	USER	restore	USER	select	19	SQL
54	1791192759	1	restore	USER	restore	USER	insert	19	SQL
55	1791192759	1	restore	USER	restore	USER	update	19	SQL
56	1791192759	1	restore	USER	restore	USER	delete	19	SQL
57	1791192759	1	restore	USER	restore	USER	select	20	SQL
58	1791192759	1	restore	USER	restore	USER	insert	20	SQL
59	1791192759	1	restore	USER	restore	USER	update	20	SQL
60	1791192759	1	restore	USER	restore	USER	delete	20	SQL
61	1791192759	1	restore	USER	restore	USER	select	21	SQL
62	1791192759	1	restore	USER	restore	USER	insert	21	SQL
63	1791192759	1	restore	USER	restore	USER	update	21	SQL
64	1791192759	1	restore	USER	restore	USER	delete	21	SQL
65	1791192759	1	restore	USER	restore	USER	select	22	SQL
66	1791192759	1	restore	USER	restore	USER	insert	22	SQL
67	1791192759	1	restore	USER	restore	USER	update	22	SQL
68	1791192759	1	restore	USER	restore	USER	delete	22	SQL
69	1791192759	1	restore	USER	restore	USER	select	23	SQL
70	1791192759	1	restore	USER	restore	USER	insert	23	SQL
71	1791192759	1	restore	USER	restore	USER	update	23	SQL
72	1791192759	1	restore	USER	restore	USER	delete	23	SQL
73	1791192759	1	restore	USER	restore	USER	select	24	SQL
74	1791192759	1	restore	USER	restore	USER	insert	24	SQL
75	1791192759	1	restore	USER	restore	USER	update	24	SQL
76	1791192759	1	restore	USER	restore	USER	delete	24	SQL
77	1791192759	1	restore	USER	restore	USER	select	25	SQL
78	1791192759	1	restore	USER	restore	USER	insert	25	SQL
79	1791192759	1	restore	USER	restore	USER	update	25	SQL
80	1791192759	1	restore	USER	restore	USER	delete	25	SQL
81	1791192759	1	restore	USER	restore	USER	select	26	SQL
82	1791192759	1	restore	USER	restore	USER	insert	26	SQL
83	1791192759	1	restore	USER	restore	USER	update	26	SQL
84	1791192759	1	restore	USER	restore	USER	delete	26	SQL
85	1791192759	1	restore	USER	restore	USER	select	27	SQL
86	1791192759	1	restore	USER	restore	USER	insert	27	SQL
87	1791192759	1	restore	USER	restore	USER	update	27	SQL
88	1791192759	1	restore	USER	restore	USER	delete	27	SQL
89	1791192759	1	restore	USER	restore	USER	select	28	SQL
90	1791192759	1	restore	USER	restore	USER	insert	28	SQL
91	1791192759	1	restore	USER	restore	USER	update	28	SQL
92	1791192759	1	restore	USER	restore	USER	delete	28	SQL
93	1791192760	1	restore	USER	restore	USER	select	29	SQL
94	1791192760	1	restore	USER	restore	USER	insert	29	SQL
95	1791192760	1	restore	USER	restore	USER	update	29	SQL
96	1791192760	1	restore	USER	restore	USER	delete	29	SQL
97	1791192760	1	restore	USER	restore	USER	select	30	SQL
98	1791192760	1	restore	USER	restore	USER	insert	30	SQL
99	1791192760	1	restore	USER	restore	USER	update	30	SQL
100	1791192760	1	restore	USER	restore	USER	delete	30	SQL
101	1791192760	1	restore	USER	restore	USER	select	31	SQL
102	1791192760	1	restore	USER	restore	USER	insert	31	SQL
103	1791192760	1	restore	USER	restore	USER	update	31	SQL
104	1791192760	1	restore	USER	restore	USER	delete	31	SQL
105	1791192760	1	restore	USER	restore	USER	select	32	SQL
106	1791192760	1	restore	USER	restore	USER	insert	32	SQL
107	1791192760	1	restore	USER	restore	USER	update	32	SQL
108	1791192760	1	restore	USER	restore	USER	delete	32	SQL
109	1791192760	1	restore	USER	restore	USER	select	33	SQL
110	1791192760	1	restore	USER	restore	USER	insert	33	SQL
111	1791192760	1	restore	USER	restore	USER	update	33	SQL
112	1791192760	1	restore	USER	restore	USER	delete	33	SQL
113	1791192760	1	restore	USER	restore	USER	select	34	SQL
114	1791192760	1	restore	USER	restore	USER	insert	34	SQL
115	1791192760	1	restore	USER	restore	USER	update	34	SQL
116	1791192760	1	restore	USER	restore	USER	delete	34	SQL
117	1791192760	1	restore	USER	restore	USER	select	35	SQL
118	1791192760	1	restore	USER	restore	USER	insert	35	SQL
119	1791192760	1	restore	USER	restore	USER	update	35	SQL
120	1791192760	1	restore	USER	restore	USER	delete	35	SQL
121	1791192760	1	restore	USER	restore	USER	select	36	SQL
122	1791192760	1	restore	USER	restore	USER	insert	36	SQL
123	1791192760	1	restore	USER	restore	USER	update	36	SQL
124	1791192760	1	restore	USER	restore	USER	delete	36	SQL
125	1791192760	1	restore	USER	restore	USER	select	37	SQL
126	1791192760	1	restore	USER	restore	USER	insert	37	SQL
127	1791192760	1	restore	USER	restore	USER	update	37	SQL
128	1791192760	1	restore	USER	restore	USER	delete	37	SQL
129	1791192760	1	restore	USER	restore	USER	select	38	SQL
130	1791192760	1	restore	USER	restore	USER	insert	38	SQL
131	1791192760	1	restore	USER	restore	USER	update	38	SQL
132	1791192760	1	restore	USER	restore	USER	delete	38	SQL
133	1791192760	1	restore	USER	restore	USER	select	39	SQL
134	1791192760	1	restore	USER	restore	USER	insert	39	SQL
135	1791192760	1	restore	USER	restore	USER	update	39	SQL
136	1791192760	1	restore	USER	restore	USER	delete	39	SQL
137	1791192760	1	restore	USER	restore	USER	select	40	SQL
138	1791192760	1	restore	USER	restore	USER	insert	40	SQL
139	1791192760	1	restore	USER	restore	USER	update	40	SQL
140	1791192760	1	restore	USER	restore	USER	delete	40	SQL
141	1791192760	1	restore	USER	restore	USER	select	41	SQL
142	1791192760	1	restore	USER	restore	USER	insert	41	SQL
143	1791192760	1	restore	USER	restore	USER	update	41	SQL
144	1791192760	1	restore	USER	restore	USER	delete	41	SQL
145	1791192760	1	restore	USER	restore	USER	select	42	SQL
146	1791192760	1	restore	USER	restore	USER	insert	42	SQL
147	1791192760	1	restore	USER	restore	USER	update	42	SQL
148	1791192760	1	restore	USER	restore	USER	delete	42	SQL
149	1791192760	1	restore	USER	restore	USER	select	43	SQL
150	1791192760	1	restore	USER	restore	USER	insert	43	SQL
151	1791192760	1	restore	USER	restore	USER	update	43	SQL
152	1791192760	1	restore	USER	restore	USER	delete	43	SQL
153	1791192760	1	restore	USER	restore	USER	select	44	SQL
154	1791192760	1	restore	USER	restore	USER	insert	44	SQL
155	1791192760	1	restore	USER	restore	USER	update	44	SQL
156	1791192760	1	restore	USER	restore	USER	delete	44	SQL
157	1791192761	1	restore	USER	restore	USER	select	45	SQL
158	1791192761	1	restore	USER	restore	USER	insert	45	SQL
159	1791192761	1	restore	USER	restore	USER	update	45	SQL
160	1791192761	1	restore	USER	restore	USER	delete	45	SQL
161	1791192761	1	restore	USER	restore	USER	select	46	SQL
162	1791192761	1	restore	USER	restore	USER	insert	46	SQL
163	1791192761	1	restore	USER	restore	USER	update	46	SQL
164	1791192761	1	restore	USER	restore	USER	delete	46	SQL
165	1791192761	1	restore	USER	restore	USER	select	47	SQL
166	1791192761	1	restore	USER	restore	USER	insert	47	SQL
167	1791192761	1	restore	USER	restore	USER	update	47	SQL
168	1791192761	1	restore	USER	restore	USER	delete	47	SQL
169	1791192761	1	restore	USER	restore	USER	select	48	SQL
170	1791192761	1	restore	USER	restore	USER	insert	48	SQL
171	1791192761	1	restore	USER	restore	USER	update	48	SQL
172	1791192761	1	restore	USER	restore	USER	delete	48	SQL
173	1791192761	1	restore	USER	restore	USER	select	49	SQL
174	1791192761	1	restore	USER	restore	USER	insert	49	SQL
175	1791192761	1	restore	USER	restore	USER	update	49	SQL
176	1791192761	1	restore	USER	restore	USER	delete	49	SQL
177	1791192761	1	restore	USER	restore	USER	select	50	SQL
178	1791192761	1	restore	USER	restore	USER	insert	50	SQL
179	1791192761	1	restore	USER	restore	USER	update	50	SQL
180	1791192761	1	restore	USER	restore	USER	delete	50	SQL
181	1791192761	1	restore	USER	restore	USER	select	51	SQL
182	1791192761	1	restore	USER	restore	USER	insert	51	SQL
183	1791192761	1	restore	USER	restore	USER	update	51	SQL
184	1791192761	1	restore	USER	restore	USER	delete	51	SQL
185	1791192761	1	restore	USER	restore	USER	select	52	SQL
186	1791192761	1	restore	USER	restore	USER	insert	52	SQL
187	1791192761	1	restore	USER	restore	USER	update	52	SQL
188	1791192761	1	restore	USER	restore	USER	delete	52	SQL
189	1791192761	1	restore	USER	restore	USER	select	53	SQL
190	1791192761	1	restore	USER	restore	USER	insert	53	SQL
191	1791192761	1	restore	USER	restore	USER	update	53	SQL
192	1791192761	1	restore	USER	restore	USER	delete	53	SQL
193	1791192761	1	restore	USER	restore	USER	select	54	SQL
194	1791192761	1	restore	USER	restore	USER	insert	54	SQL
195	1791192761	1	restore	USER	restore	USER	update	54	SQL
196	1791192761	1	restore	USER	restore	USER	delete	54	SQL
197	1791194632	1	restore	USER	restore	USER	select	55	SQL
198	1791194632	1	restore	USER	restore	USER	insert	55	SQL
199	1791194632	1	restore	USER	restore	USER	update	55	SQL
200	1791194632	1	restore	USER	restore	USER	delete	55	SQL
201	1791194632	1	restore	USER	restore	USER	select	56	SQL
202	1791194632	1	restore	USER	restore	USER	insert	56	SQL
203	1791194632	1	restore	USER	restore	USER	update	56	SQL
204	1791194632	1	restore	USER	restore	USER	delete	56	SQL
205	1791194632	1	restore	USER	restore	USER	select	57	SQL
206	1791194632	1	restore	USER	restore	USER	insert	57	SQL
207	1791194632	1	restore	USER	restore	USER	update	57	SQL
208	1791194632	1	restore	USER	restore	USER	delete	57	SQL
209	1791194632	1	restore	USER	restore	USER	select	58	SQL
210	1791194632	1	restore	USER	restore	USER	insert	58	SQL
211	1791194632	1	restore	USER	restore	USER	update	58	SQL
212	1791194632	1	restore	USER	restore	USER	delete	58	SQL
213	1791194632	1	restore	USER	restore	USER	select	59	SQL
214	1791194632	1	restore	USER	restore	USER	insert	59	SQL
215	1791194632	1	restore	USER	restore	USER	update	59	SQL
216	1791194632	1	restore	USER	restore	USER	delete	59	SQL
217	1791194633	1	restore	USER	restore	USER	select	60	SQL
218	1791194633	1	restore	USER	restore	USER	insert	60	SQL
219	1791194633	1	restore	USER	restore	USER	update	60	SQL
220	1791194633	1	restore	USER	restore	USER	delete	60	SQL
221	1791194633	1	restore	USER	restore	USER	select	61	SQL
222	1791194633	1	restore	USER	restore	USER	insert	61	SQL
223	1791194633	1	restore	USER	restore	USER	update	61	SQL
224	1791194633	1	restore	USER	restore	USER	delete	61	SQL
225	1791194633	1	restore	USER	restore	USER	select	62	SQL
226	1791194633	1	restore	USER	restore	USER	insert	62	SQL
227	1791194633	1	restore	USER	restore	USER	update	62	SQL
228	1791194633	1	restore	USER	restore	USER	delete	62	SQL
229	1791194633	1	restore	USER	restore	USER	select	63	SQL
230	1791194633	1	restore	USER	restore	USER	insert	63	SQL
231	1791194633	1	restore	USER	restore	USER	update	63	SQL
232	1791194633	1	restore	USER	restore	USER	delete	63	SQL
241	1791436513	1	root	USER	root	USER	select	71	SQL
242	1791436513	1	root	USER	root	USER	insert	71	SQL
243	1791436513	1	root	USER	root	USER	update	71	SQL
244	1791436513	1	root	USER	root	USER	delete	71	SQL
245	1791436585	1	root	USER	root	USER	select	72	SQL
246	1791436585	1	root	USER	root	USER	insert	72	SQL
247	1791436585	1	root	USER	root	USER	update	72	SQL
248	1791436585	1	root	USER	root	USER	delete	72	SQL
249	1791442603	1	root	USER	root	USER	select	73	SQL
250	1791442603	1	root	USER	root	USER	insert	73	SQL
251	1791442603	1	root	USER	root	USER	update	73	SQL
252	1791442603	1	root	USER	root	USER	delete	73	SQL
253	1791442621	1	root	USER	root	USER	select	74	SQL
254	1791442621	1	root	USER	root	USER	insert	74	SQL
255	1791442621	1	root	USER	root	USER	update	74	SQL
256	1791442621	1	root	USER	root	USER	delete	74	SQL
257	1791443736	1	root	USER	root	USER	select	75	SQL
258	1791443736	1	root	USER	root	USER	insert	75	SQL
259	1791443736	1	root	USER	root	USER	update	75	SQL
260	1791443736	1	root	USER	root	USER	delete	75	SQL
261	1791443737	1	root	USER	root	USER	select	76	SQL
262	1791443737	1	root	USER	root	USER	insert	76	SQL
263	1791443737	1	root	USER	root	USER	update	76	SQL
264	1791443737	1	root	USER	root	USER	delete	76	SQL
265	1791443737	1	root	USER	root	USER	select	77	SQL
266	1791443737	1	root	USER	root	USER	insert	77	SQL
267	1791443737	1	root	USER	root	USER	update	77	SQL
268	1791443737	1	root	USER	root	USER	delete	77	SQL
269	1791444626	1	root	USER	root	USER	select	78	SQL
270	1791444626	1	root	USER	root	USER	insert	78	SQL
271	1791444626	1	root	USER	root	USER	update	78	SQL
272	1791444626	1	root	USER	root	USER	delete	78	SQL
281	1792040394	1	root	USER	root	USER	select	81	SQL
282	1792040394	1	root	USER	root	USER	insert	81	SQL
283	1792040394	1	root	USER	root	USER	update	81	SQL
284	1792040394	1	root	USER	root	USER	delete	81	SQL
\.


--
-- Data for Name: TXNS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."TXNS" ("TXN_ID", "TXN_STATE", "TXN_STARTED", "TXN_LAST_HEARTBEAT", "TXN_USER", "TXN_HOST", "TXN_AGENT_INFO", "TXN_META_INFO", "TXN_HEARTBEAT_COUNT", "TXN_TYPE") FROM stdin;
0	c	0	0			\N	\N	\N	\N
\.


--
-- Data for Name: TXN_COMPONENTS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."TXN_COMPONENTS" ("TC_TXNID", "TC_DATABASE", "TC_TABLE", "TC_PARTITION", "TC_OPERATION_TYPE", "TC_WRITEID") FROM stdin;
\.


--
-- Data for Name: TXN_LOCK_TBL; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."TXN_LOCK_TBL" ("TXN_LOCK") FROM stdin;
1
\.


--
-- Data for Name: TXN_TO_WRITE_ID; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."TXN_TO_WRITE_ID" ("T2W_TXNID", "T2W_DATABASE", "T2W_TABLE", "T2W_WRITEID") FROM stdin;
\.


--
-- Data for Name: TXN_WRITE_NOTIFICATION_LOG; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."TXN_WRITE_NOTIFICATION_LOG" ("WNL_ID", "WNL_TXNID", "WNL_WRITEID", "WNL_DATABASE", "WNL_TABLE", "WNL_PARTITION", "WNL_TABLE_OBJ", "WNL_PARTITION_OBJ", "WNL_FILES", "WNL_EVENT_TIME") FROM stdin;
\.


--
-- Data for Name: TYPES; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."TYPES" ("TYPES_ID", "TYPE_NAME", "TYPE1", "TYPE2") FROM stdin;
\.


--
-- Data for Name: TYPE_FIELDS; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."TYPE_FIELDS" ("TYPE_NAME", "COMMENT", "FIELD_NAME", "FIELD_TYPE", "INTEGER_IDX") FROM stdin;
\.


--
-- Data for Name: VERSION; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."VERSION" ("VER_ID", "SCHEMA_VERSION", "VERSION_COMMENT") FROM stdin;
1	4.2.0	Hive release version 4.2.0
\.


--
-- Data for Name: WM_MAPPING; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."WM_MAPPING" ("MAPPING_ID", "RP_ID", "ENTITY_TYPE", "ENTITY_NAME", "POOL_ID", "ORDERING") FROM stdin;
\.


--
-- Data for Name: WM_POOL; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."WM_POOL" ("POOL_ID", "RP_ID", "PATH", "ALLOC_FRACTION", "QUERY_PARALLELISM", "SCHEDULING_POLICY") FROM stdin;
\.


--
-- Data for Name: WM_POOL_TO_TRIGGER; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."WM_POOL_TO_TRIGGER" ("POOL_ID", "TRIGGER_ID") FROM stdin;
\.


--
-- Data for Name: WM_RESOURCEPLAN; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."WM_RESOURCEPLAN" ("RP_ID", "NAME", "NS", "QUERY_PARALLELISM", "STATUS", "DEFAULT_POOL_ID") FROM stdin;
\.


--
-- Data for Name: WM_TRIGGER; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."WM_TRIGGER" ("TRIGGER_ID", "RP_ID", "NAME", "TRIGGER_EXPRESSION", "ACTION_EXPRESSION", "IS_IN_UNMANAGED") FROM stdin;
\.


--
-- Data for Name: WRITE_SET; Type: TABLE DATA; Schema: public; Owner: hive
--

COPY public."WRITE_SET" ("WS_DATABASE", "WS_TABLE", "WS_PARTITION", "WS_TXNID", "WS_COMMIT_ID", "WS_OPERATION_TYPE") FROM stdin;
\.


--
-- Name: MASTER_KEYS_KEY_ID_seq; Type: SEQUENCE SET; Schema: public; Owner: hive
--

SELECT pg_catalog.setval('public."MASTER_KEYS_KEY_ID_seq"', 1, false);


--
-- Name: TXNS_TXN_ID_seq; Type: SEQUENCE SET; Schema: public; Owner: hive
--

SELECT pg_catalog.setval('public."TXNS_TXN_ID_seq"', 1, false);


--
-- Name: AUX_TABLE AUX_TABLE_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."AUX_TABLE"
    ADD CONSTRAINT "AUX_TABLE_pkey" PRIMARY KEY ("MT_KEY1", "MT_KEY2");


--
-- Name: BUCKETING_COLS BUCKETING_COLS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."BUCKETING_COLS"
    ADD CONSTRAINT "BUCKETING_COLS_pkey" PRIMARY KEY ("SD_ID", "INTEGER_IDX");


--
-- Name: CATALOG_PARAMS CATALOG_PARAMS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."CATALOG_PARAMS"
    ADD CONSTRAINT "CATALOG_PARAMS_pkey" PRIMARY KEY ("CTLG_ID", "PARAM_KEY");


--
-- Name: CDS CDS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."CDS"
    ADD CONSTRAINT "CDS_pkey" PRIMARY KEY ("CD_ID");


--
-- Name: COLUMNS_V2 COLUMNS_V2_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."COLUMNS_V2"
    ADD CONSTRAINT "COLUMNS_V2_pkey" PRIMARY KEY ("CD_ID", "COLUMN_NAME");


--
-- Name: COMPACTION_QUEUE COMPACTION_QUEUE_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."COMPACTION_QUEUE"
    ADD CONSTRAINT "COMPACTION_QUEUE_pkey" PRIMARY KEY ("CQ_ID");


--
-- Name: COMPLETED_COMPACTIONS COMPLETED_COMPACTIONS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."COMPLETED_COMPACTIONS"
    ADD CONSTRAINT "COMPLETED_COMPACTIONS_pkey" PRIMARY KEY ("CC_ID");


--
-- Name: CTLGS CTLGS_NAME_key; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."CTLGS"
    ADD CONSTRAINT "CTLGS_NAME_key" UNIQUE ("NAME");


--
-- Name: CTLGS CTLGS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."CTLGS"
    ADD CONSTRAINT "CTLGS_pkey" PRIMARY KEY ("CTLG_ID");


--
-- Name: DATABASE_PARAMS DATABASE_PARAMS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."DATABASE_PARAMS"
    ADD CONSTRAINT "DATABASE_PARAMS_pkey" PRIMARY KEY ("DB_ID", "PARAM_KEY");


--
-- Name: DATACONNECTORS DATACONNECTORS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."DATACONNECTORS"
    ADD CONSTRAINT "DATACONNECTORS_pkey" PRIMARY KEY ("NAME");


--
-- Name: DATACONNECTOR_PARAMS DATACONNECTOR_PARAMS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."DATACONNECTOR_PARAMS"
    ADD CONSTRAINT "DATACONNECTOR_PARAMS_pkey" PRIMARY KEY ("NAME", "PARAM_KEY");


--
-- Name: DB_PRIVS DBPRIVILEGEINDEX; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."DB_PRIVS"
    ADD CONSTRAINT "DBPRIVILEGEINDEX" UNIQUE ("AUTHORIZER", "DB_ID", "PRINCIPAL_NAME", "PRINCIPAL_TYPE", "DB_PRIV", "GRANTOR", "GRANTOR_TYPE");


--
-- Name: DBS DBS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."DBS"
    ADD CONSTRAINT "DBS_pkey" PRIMARY KEY ("DB_ID");


--
-- Name: DB_PRIVS DB_PRIVS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."DB_PRIVS"
    ADD CONSTRAINT "DB_PRIVS_pkey" PRIMARY KEY ("DB_GRANT_ID");


--
-- Name: DC_PRIVS DCPRIVILEGEINDEX; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."DC_PRIVS"
    ADD CONSTRAINT "DCPRIVILEGEINDEX" UNIQUE ("AUTHORIZER", "NAME", "PRINCIPAL_NAME", "PRINCIPAL_TYPE", "DC_PRIV", "GRANTOR", "GRANTOR_TYPE");


--
-- Name: DC_PRIVS DC_PRIVS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."DC_PRIVS"
    ADD CONSTRAINT "DC_PRIVS_pkey" PRIMARY KEY ("DC_GRANT_ID");


--
-- Name: DELEGATION_TOKENS DELEGATION_TOKENS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."DELEGATION_TOKENS"
    ADD CONSTRAINT "DELEGATION_TOKENS_pkey" PRIMARY KEY ("TOKEN_IDENT");


--
-- Name: FUNCS FUNCS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."FUNCS"
    ADD CONSTRAINT "FUNCS_pkey" PRIMARY KEY ("FUNC_ID");


--
-- Name: FUNC_RU FUNC_RU_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."FUNC_RU"
    ADD CONSTRAINT "FUNC_RU_pkey" PRIMARY KEY ("FUNC_ID", "INTEGER_IDX");


--
-- Name: GLOBAL_PRIVS GLOBALPRIVILEGEINDEX; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."GLOBAL_PRIVS"
    ADD CONSTRAINT "GLOBALPRIVILEGEINDEX" UNIQUE ("AUTHORIZER", "PRINCIPAL_NAME", "PRINCIPAL_TYPE", "USER_PRIV", "GRANTOR", "GRANTOR_TYPE");


--
-- Name: GLOBAL_PRIVS GLOBAL_PRIVS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."GLOBAL_PRIVS"
    ADD CONSTRAINT "GLOBAL_PRIVS_pkey" PRIMARY KEY ("USER_GRANT_ID");


--
-- Name: HIVE_LOCKS HIVE_LOCKS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."HIVE_LOCKS"
    ADD CONSTRAINT "HIVE_LOCKS_pkey" PRIMARY KEY ("HL_LOCK_EXT_ID", "HL_LOCK_INT_ID");


--
-- Name: I_SCHEMA I_SCHEMA_NAME_key; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."I_SCHEMA"
    ADD CONSTRAINT "I_SCHEMA_NAME_key" UNIQUE ("NAME");


--
-- Name: I_SCHEMA I_SCHEMA_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."I_SCHEMA"
    ADD CONSTRAINT "I_SCHEMA_pkey" PRIMARY KEY ("SCHEMA_ID");


--
-- Name: MASTER_KEYS MASTER_KEYS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."MASTER_KEYS"
    ADD CONSTRAINT "MASTER_KEYS_pkey" PRIMARY KEY ("KEY_ID");


--
-- Name: MATERIALIZATION_REBUILD_LOCKS MATERIALIZATION_REBUILD_LOCKS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."MATERIALIZATION_REBUILD_LOCKS"
    ADD CONSTRAINT "MATERIALIZATION_REBUILD_LOCKS_pkey" PRIMARY KEY ("MRL_TXN_ID");


--
-- Name: MIN_HISTORY_LEVEL MIN_HISTORY_LEVEL_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."MIN_HISTORY_LEVEL"
    ADD CONSTRAINT "MIN_HISTORY_LEVEL_pkey" PRIMARY KEY ("MHL_TXNID");


--
-- Name: MV_CREATION_METADATA MV_CREATION_METADATA_PK; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."MV_CREATION_METADATA"
    ADD CONSTRAINT "MV_CREATION_METADATA_PK" PRIMARY KEY ("MV_CREATION_METADATA_ID");


--
-- Name: MV_TABLES_USED MV_TABLES_USED_PK; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."MV_TABLES_USED"
    ADD CONSTRAINT "MV_TABLES_USED_PK" PRIMARY KEY ("TBL_ID", "MV_CREATION_METADATA_ID");


--
-- Name: NOTIFICATION_LOG NOTIFICATION_LOG_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."NOTIFICATION_LOG"
    ADD CONSTRAINT "NOTIFICATION_LOG_pkey" PRIMARY KEY ("NL_ID");


--
-- Name: NOTIFICATION_SEQUENCE NOTIFICATION_SEQUENCE_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."NOTIFICATION_SEQUENCE"
    ADD CONSTRAINT "NOTIFICATION_SEQUENCE_pkey" PRIMARY KEY ("NNI_ID");


--
-- Name: NUCLEUS_TABLES NUCLEUS_TABLES_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."NUCLEUS_TABLES"
    ADD CONSTRAINT "NUCLEUS_TABLES_pkey" PRIMARY KEY ("CLASS_NAME");


--
-- Name: PACKAGES PACKAGES_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PACKAGES"
    ADD CONSTRAINT "PACKAGES_pkey" PRIMARY KEY ("PKG_ID");


--
-- Name: PARTITIONS PARTITIONS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PARTITIONS"
    ADD CONSTRAINT "PARTITIONS_pkey" PRIMARY KEY ("PART_ID");


--
-- Name: PARTITION_EVENTS PARTITION_EVENTS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PARTITION_EVENTS"
    ADD CONSTRAINT "PARTITION_EVENTS_pkey" PRIMARY KEY ("PART_NAME_ID");


--
-- Name: PARTITION_KEYS PARTITION_KEYS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PARTITION_KEYS"
    ADD CONSTRAINT "PARTITION_KEYS_pkey" PRIMARY KEY ("TBL_ID", "PKEY_NAME");


--
-- Name: PARTITION_KEY_VALS PARTITION_KEY_VALS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PARTITION_KEY_VALS"
    ADD CONSTRAINT "PARTITION_KEY_VALS_pkey" PRIMARY KEY ("PART_ID", "INTEGER_IDX");


--
-- Name: PARTITION_PARAMS PARTITION_PARAMS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PARTITION_PARAMS"
    ADD CONSTRAINT "PARTITION_PARAMS_pkey" PRIMARY KEY ("PART_ID", "PARAM_KEY");


--
-- Name: PART_COL_PRIVS PART_COL_PRIVS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PART_COL_PRIVS"
    ADD CONSTRAINT "PART_COL_PRIVS_pkey" PRIMARY KEY ("PART_COLUMN_GRANT_ID");


--
-- Name: PART_COL_STATS PART_COL_STATS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PART_COL_STATS"
    ADD CONSTRAINT "PART_COL_STATS_pkey" PRIMARY KEY ("CS_ID");


--
-- Name: PART_PRIVS PART_PRIVS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PART_PRIVS"
    ADD CONSTRAINT "PART_PRIVS_pkey" PRIMARY KEY ("PART_GRANT_ID");


--
-- Name: METASTORE_DB_PROPERTIES PROPERTY_KEY_PK; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."METASTORE_DB_PROPERTIES"
    ADD CONSTRAINT "PROPERTY_KEY_PK" PRIMARY KEY ("PROPERTY_KEY");


--
-- Name: REPLICATION_METRICS REPLICATION_METRICS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."REPLICATION_METRICS"
    ADD CONSTRAINT "REPLICATION_METRICS_pkey" PRIMARY KEY ("RM_SCHEDULED_EXECUTION_ID");


--
-- Name: REPL_TXN_MAP REPL_TXN_MAP_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."REPL_TXN_MAP"
    ADD CONSTRAINT "REPL_TXN_MAP_pkey" PRIMARY KEY ("RTM_REPL_POLICY", "RTM_SRC_TXN_ID");


--
-- Name: ROLES ROLEENTITYINDEX; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."ROLES"
    ADD CONSTRAINT "ROLEENTITYINDEX" UNIQUE ("ROLE_NAME");


--
-- Name: ROLES ROLES_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."ROLES"
    ADD CONSTRAINT "ROLES_pkey" PRIMARY KEY ("ROLE_ID");


--
-- Name: ROLE_MAP ROLE_MAP_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."ROLE_MAP"
    ADD CONSTRAINT "ROLE_MAP_pkey" PRIMARY KEY ("ROLE_GRANT_ID");


--
-- Name: RUNTIME_STATS RUNTIME_STATS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."RUNTIME_STATS"
    ADD CONSTRAINT "RUNTIME_STATS_pkey" PRIMARY KEY ("RS_ID");


--
-- Name: SCHEDULED_EXECUTIONS SCHEDULED_EXECUTIONS_PK; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SCHEDULED_EXECUTIONS"
    ADD CONSTRAINT "SCHEDULED_EXECUTIONS_PK" PRIMARY KEY ("SCHEDULED_EXECUTION_ID");


--
-- Name: SCHEDULED_QUERIES SCHEDULED_QUERIES_PK; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SCHEDULED_QUERIES"
    ADD CONSTRAINT "SCHEDULED_QUERIES_PK" PRIMARY KEY ("SCHEDULED_QUERY_ID");


--
-- Name: SCHEMA_VERSION SCHEMA_VERSION_SCHEMA_ID_VERSION_key; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SCHEMA_VERSION"
    ADD CONSTRAINT "SCHEMA_VERSION_SCHEMA_ID_VERSION_key" UNIQUE ("SCHEMA_ID", "VERSION");


--
-- Name: SCHEMA_VERSION SCHEMA_VERSION_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SCHEMA_VERSION"
    ADD CONSTRAINT "SCHEMA_VERSION_pkey" PRIMARY KEY ("SCHEMA_VERSION_ID");


--
-- Name: SDS SDS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SDS"
    ADD CONSTRAINT "SDS_pkey" PRIMARY KEY ("SD_ID");


--
-- Name: SD_PARAMS SD_PARAMS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SD_PARAMS"
    ADD CONSTRAINT "SD_PARAMS_pkey" PRIMARY KEY ("SD_ID", "PARAM_KEY");


--
-- Name: SEQUENCE_TABLE SEQUENCE_TABLE_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SEQUENCE_TABLE"
    ADD CONSTRAINT "SEQUENCE_TABLE_pkey" PRIMARY KEY ("SEQUENCE_NAME");


--
-- Name: SERDES SERDES_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SERDES"
    ADD CONSTRAINT "SERDES_pkey" PRIMARY KEY ("SERDE_ID");


--
-- Name: SERDE_PARAMS SERDE_PARAMS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SERDE_PARAMS"
    ADD CONSTRAINT "SERDE_PARAMS_pkey" PRIMARY KEY ("SERDE_ID", "PARAM_KEY");


--
-- Name: SKEWED_COL_NAMES SKEWED_COL_NAMES_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SKEWED_COL_NAMES"
    ADD CONSTRAINT "SKEWED_COL_NAMES_pkey" PRIMARY KEY ("SD_ID", "INTEGER_IDX");


--
-- Name: SKEWED_COL_VALUE_LOC_MAP SKEWED_COL_VALUE_LOC_MAP_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SKEWED_COL_VALUE_LOC_MAP"
    ADD CONSTRAINT "SKEWED_COL_VALUE_LOC_MAP_pkey" PRIMARY KEY ("SD_ID", "STRING_LIST_ID_KID");


--
-- Name: SKEWED_STRING_LIST_VALUES SKEWED_STRING_LIST_VALUES_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SKEWED_STRING_LIST_VALUES"
    ADD CONSTRAINT "SKEWED_STRING_LIST_VALUES_pkey" PRIMARY KEY ("STRING_LIST_ID", "INTEGER_IDX");


--
-- Name: SKEWED_STRING_LIST SKEWED_STRING_LIST_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SKEWED_STRING_LIST"
    ADD CONSTRAINT "SKEWED_STRING_LIST_pkey" PRIMARY KEY ("STRING_LIST_ID");


--
-- Name: SKEWED_VALUES SKEWED_VALUES_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SKEWED_VALUES"
    ADD CONSTRAINT "SKEWED_VALUES_pkey" PRIMARY KEY ("SD_ID_OID", "INTEGER_IDX");


--
-- Name: SORT_COLS SORT_COLS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SORT_COLS"
    ADD CONSTRAINT "SORT_COLS_pkey" PRIMARY KEY ("SD_ID", "INTEGER_IDX");


--
-- Name: STORED_PROCS STORED_PROCS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."STORED_PROCS"
    ADD CONSTRAINT "STORED_PROCS_pkey" PRIMARY KEY ("SP_ID");


--
-- Name: TABLE_PARAMS TABLE_PARAMS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TABLE_PARAMS"
    ADD CONSTRAINT "TABLE_PARAMS_pkey" PRIMARY KEY ("TBL_ID", "PARAM_KEY");


--
-- Name: TAB_COL_STATS TAB_COL_STATS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TAB_COL_STATS"
    ADD CONSTRAINT "TAB_COL_STATS_pkey" PRIMARY KEY ("CS_ID");


--
-- Name: TBLS TBLS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TBLS"
    ADD CONSTRAINT "TBLS_pkey" PRIMARY KEY ("TBL_ID");


--
-- Name: TBL_COL_PRIVS TBL_COL_PRIVS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TBL_COL_PRIVS"
    ADD CONSTRAINT "TBL_COL_PRIVS_pkey" PRIMARY KEY ("TBL_COLUMN_GRANT_ID");


--
-- Name: TBL_PRIVS TBL_PRIVS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TBL_PRIVS"
    ADD CONSTRAINT "TBL_PRIVS_pkey" PRIMARY KEY ("TBL_GRANT_ID");


--
-- Name: TXNS TXNS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TXNS"
    ADD CONSTRAINT "TXNS_pkey" PRIMARY KEY ("TXN_ID");


--
-- Name: TXN_WRITE_NOTIFICATION_LOG TXN_WRITE_NOTIFICATION_LOG_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TXN_WRITE_NOTIFICATION_LOG"
    ADD CONSTRAINT "TXN_WRITE_NOTIFICATION_LOG_pkey" PRIMARY KEY ("WNL_TXNID", "WNL_DATABASE", "WNL_TABLE", "WNL_PARTITION");


--
-- Name: TYPES TYPES_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TYPES"
    ADD CONSTRAINT "TYPES_pkey" PRIMARY KEY ("TYPES_ID");


--
-- Name: TYPE_FIELDS TYPE_FIELDS_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TYPE_FIELDS"
    ADD CONSTRAINT "TYPE_FIELDS_pkey" PRIMARY KEY ("TYPE_NAME", "FIELD_NAME");


--
-- Name: PARTITIONS UNIQUEPARTITION; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PARTITIONS"
    ADD CONSTRAINT "UNIQUEPARTITION" UNIQUE ("TBL_ID", "PART_NAME");


--
-- Name: TBLS UNIQUETABLE; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TBLS"
    ADD CONSTRAINT "UNIQUETABLE" UNIQUE ("DB_ID", "TBL_NAME");


--
-- Name: DBS UNIQUE_DATABASE; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."DBS"
    ADD CONSTRAINT "UNIQUE_DATABASE" UNIQUE ("NAME", "CTLG_NAME");


--
-- Name: TYPES UNIQUE_TYPE; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TYPES"
    ADD CONSTRAINT "UNIQUE_TYPE" UNIQUE ("TYPE_NAME");


--
-- Name: WM_MAPPING UNIQUE_WM_MAPPING; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_MAPPING"
    ADD CONSTRAINT "UNIQUE_WM_MAPPING" UNIQUE ("RP_ID", "ENTITY_TYPE", "ENTITY_NAME");


--
-- Name: WM_POOL UNIQUE_WM_POOL; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_POOL"
    ADD CONSTRAINT "UNIQUE_WM_POOL" UNIQUE ("RP_ID", "PATH");


--
-- Name: WM_RESOURCEPLAN UNIQUE_WM_RESOURCEPLAN; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_RESOURCEPLAN"
    ADD CONSTRAINT "UNIQUE_WM_RESOURCEPLAN" UNIQUE ("NS", "NAME");


--
-- Name: WM_TRIGGER UNIQUE_WM_TRIGGER; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_TRIGGER"
    ADD CONSTRAINT "UNIQUE_WM_TRIGGER" UNIQUE ("RP_ID", "NAME");


--
-- Name: ROLE_MAP USERROLEMAPINDEX; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."ROLE_MAP"
    ADD CONSTRAINT "USERROLEMAPINDEX" UNIQUE ("PRINCIPAL_NAME", "ROLE_ID", "GRANTOR", "GRANTOR_TYPE");


--
-- Name: VERSION VERSION_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."VERSION"
    ADD CONSTRAINT "VERSION_pkey" PRIMARY KEY ("VER_ID");


--
-- Name: WM_MAPPING WM_MAPPING_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_MAPPING"
    ADD CONSTRAINT "WM_MAPPING_pkey" PRIMARY KEY ("MAPPING_ID");


--
-- Name: WM_POOL_TO_TRIGGER WM_POOL_TO_TRIGGER_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_POOL_TO_TRIGGER"
    ADD CONSTRAINT "WM_POOL_TO_TRIGGER_pkey" PRIMARY KEY ("POOL_ID", "TRIGGER_ID");


--
-- Name: WM_POOL WM_POOL_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_POOL"
    ADD CONSTRAINT "WM_POOL_pkey" PRIMARY KEY ("POOL_ID");


--
-- Name: WM_RESOURCEPLAN WM_RESOURCEPLAN_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_RESOURCEPLAN"
    ADD CONSTRAINT "WM_RESOURCEPLAN_pkey" PRIMARY KEY ("RP_ID");


--
-- Name: WM_TRIGGER WM_TRIGGER_pkey; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_TRIGGER"
    ADD CONSTRAINT "WM_TRIGGER_pkey" PRIMARY KEY ("TRIGGER_ID");


--
-- Name: KEY_CONSTRAINTS constraints_pk; Type: CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."KEY_CONSTRAINTS"
    ADD CONSTRAINT constraints_pk PRIMARY KEY ("PARENT_TBL_ID", "CONSTRAINT_NAME", "POSITION");


--
-- Name: BUCKETING_COLS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "BUCKETING_COLS_N49" ON public."BUCKETING_COLS" USING btree ("SD_ID");


--
-- Name: CATALOG_PARAMS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "CATALOG_PARAMS_N49" ON public."CATALOG_PARAMS" USING btree ("CTLG_ID");


--
-- Name: COMPLETED_COMPACTIONS_RES; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "COMPLETED_COMPACTIONS_RES" ON public."COMPLETED_COMPACTIONS" USING btree ("CC_DATABASE", "CC_TABLE", "CC_PARTITION");


--
-- Name: CONSTRAINTS_CONSTRAINT_TYPE_INDEX; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "CONSTRAINTS_CONSTRAINT_TYPE_INDEX" ON public."KEY_CONSTRAINTS" USING btree ("CONSTRAINT_TYPE");


--
-- Name: CONSTRAINTS_PARENT_TBLID_INDEX; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "CONSTRAINTS_PARENT_TBLID_INDEX" ON public."KEY_CONSTRAINTS" USING btree ("PARENT_TBL_ID");


--
-- Name: DATABASE_PARAMS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "DATABASE_PARAMS_N49" ON public."DATABASE_PARAMS" USING btree ("DB_ID");


--
-- Name: DB_PRIVS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "DB_PRIVS_N49" ON public."DB_PRIVS" USING btree ("DB_ID");


--
-- Name: DC_PRIVS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "DC_PRIVS_N49" ON public."DC_PRIVS" USING btree ("NAME");


--
-- Name: DUMP_IDX; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "DUMP_IDX" ON public."REPLICATION_METRICS" USING btree ("RM_DUMP_EXECUTION_ID");


--
-- Name: FUNCS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "FUNCS_N49" ON public."FUNCS" USING btree ("DB_ID");


--
-- Name: FUNC_RU_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "FUNC_RU_N49" ON public."FUNC_RU" USING btree ("FUNC_ID");


--
-- Name: IDX_RUNTIME_STATS_CREATE_TIME; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "IDX_RUNTIME_STATS_CREATE_TIME" ON public."RUNTIME_STATS" USING btree ("CREATE_TIME");


--
-- Name: KEY_CONSTRAINTS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "KEY_CONSTRAINTS_N49" ON public."KEY_CONSTRAINTS" USING btree ("CHILD_CD_ID");


--
-- Name: KEY_CONSTRAINTS_N50; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "KEY_CONSTRAINTS_N50" ON public."KEY_CONSTRAINTS" USING btree ("CHILD_TBL_ID");


--
-- Name: KEY_CONSTRAINTS_N51; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "KEY_CONSTRAINTS_N51" ON public."KEY_CONSTRAINTS" USING btree ("PARENT_CD_ID");


--
-- Name: LASTUPDATETIMEINDEX; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "LASTUPDATETIMEINDEX" ON public."SCHEDULED_EXECUTIONS" USING btree ("LAST_UPDATE_TIME");


--
-- Name: MIN_HISTORY_LEVEL_IDX; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "MIN_HISTORY_LEVEL_IDX" ON public."MIN_HISTORY_LEVEL" USING btree ("MHL_MIN_OPEN_TXNID");


--
-- Name: MV_UNIQUE_TABLE; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "MV_UNIQUE_TABLE" ON public."MV_CREATION_METADATA" USING btree ("TBL_NAME", "DB_NAME");


--
-- Name: NEXTEXECUTIONINDEX; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "NEXTEXECUTIONINDEX" ON public."SCHEDULED_QUERIES" USING btree ("ENABLED", "CLUSTER_NAMESPACE", "NEXT_EXECUTION");


--
-- Name: NEXT_WRITE_ID_IDX; Type: INDEX; Schema: public; Owner: hive
--

CREATE UNIQUE INDEX "NEXT_WRITE_ID_IDX" ON public."NEXT_WRITE_ID" USING btree ("NWI_DATABASE", "NWI_TABLE");


--
-- Name: NOTIFICATION_LOG_EVENT_ID; Type: INDEX; Schema: public; Owner: hive
--

CREATE UNIQUE INDEX "NOTIFICATION_LOG_EVENT_ID" ON public."NOTIFICATION_LOG" USING btree ("EVENT_ID");


--
-- Name: PARTITIONCOLUMNPRIVILEGEINDEX; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "PARTITIONCOLUMNPRIVILEGEINDEX" ON public."PART_COL_PRIVS" USING btree ("AUTHORIZER", "PART_ID", "COLUMN_NAME", "PRINCIPAL_NAME", "PRINCIPAL_TYPE", "PART_COL_PRIV", "GRANTOR", "GRANTOR_TYPE");


--
-- Name: PARTITIONEVENTINDEX; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "PARTITIONEVENTINDEX" ON public."PARTITION_EVENTS" USING btree ("PARTITION_NAME");


--
-- Name: PARTITIONS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "PARTITIONS_N49" ON public."PARTITIONS" USING btree ("TBL_ID");


--
-- Name: PARTITIONS_N50; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "PARTITIONS_N50" ON public."PARTITIONS" USING btree ("SD_ID");


--
-- Name: PARTITION_KEYS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "PARTITION_KEYS_N49" ON public."PARTITION_KEYS" USING btree ("TBL_ID");


--
-- Name: PARTITION_KEY_VALS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "PARTITION_KEY_VALS_N49" ON public."PARTITION_KEY_VALS" USING btree ("PART_ID");


--
-- Name: PARTITION_PARAMS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "PARTITION_PARAMS_N49" ON public."PARTITION_PARAMS" USING btree ("PART_ID");


--
-- Name: PARTPRIVILEGEINDEX; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "PARTPRIVILEGEINDEX" ON public."PART_PRIVS" USING btree ("AUTHORIZER", "PART_ID", "PRINCIPAL_NAME", "PRINCIPAL_TYPE", "PART_PRIV", "GRANTOR", "GRANTOR_TYPE");


--
-- Name: PART_COL_PRIVS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "PART_COL_PRIVS_N49" ON public."PART_COL_PRIVS" USING btree ("PART_ID");


--
-- Name: PART_PRIVS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "PART_PRIVS_N49" ON public."PART_PRIVS" USING btree ("PART_ID");


--
-- Name: PCS_STATS_IDX; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "PCS_STATS_IDX" ON public."PART_COL_STATS" USING btree ("PART_ID", "COLUMN_NAME");


--
-- Name: POLICY_IDX; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "POLICY_IDX" ON public."REPLICATION_METRICS" USING btree ("RM_POLICY");


--
-- Name: ROLE_MAP_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "ROLE_MAP_N49" ON public."ROLE_MAP" USING btree ("ROLE_ID");


--
-- Name: SCHEDULED_QUERIES_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "SCHEDULED_QUERIES_N49" ON public."SCHEDULED_QUERIES" USING btree ("ACTIVE_EXECUTION_ID");


--
-- Name: SDS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "SDS_N49" ON public."SDS" USING btree ("SERDE_ID");


--
-- Name: SDS_N50; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "SDS_N50" ON public."SDS" USING btree ("CD_ID");


--
-- Name: SD_PARAMS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "SD_PARAMS_N49" ON public."SD_PARAMS" USING btree ("SD_ID");


--
-- Name: SERDE_PARAMS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "SERDE_PARAMS_N49" ON public."SERDE_PARAMS" USING btree ("SERDE_ID");


--
-- Name: SKEWED_COL_NAMES_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "SKEWED_COL_NAMES_N49" ON public."SKEWED_COL_NAMES" USING btree ("SD_ID");


--
-- Name: SKEWED_COL_VALUE_LOC_MAP_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "SKEWED_COL_VALUE_LOC_MAP_N49" ON public."SKEWED_COL_VALUE_LOC_MAP" USING btree ("STRING_LIST_ID_KID");


--
-- Name: SKEWED_COL_VALUE_LOC_MAP_N50; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "SKEWED_COL_VALUE_LOC_MAP_N50" ON public."SKEWED_COL_VALUE_LOC_MAP" USING btree ("SD_ID");


--
-- Name: SKEWED_STRING_LIST_VALUES_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "SKEWED_STRING_LIST_VALUES_N49" ON public."SKEWED_STRING_LIST_VALUES" USING btree ("STRING_LIST_ID");


--
-- Name: SKEWED_VALUES_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "SKEWED_VALUES_N49" ON public."SKEWED_VALUES" USING btree ("SD_ID_OID");


--
-- Name: SKEWED_VALUES_N50; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "SKEWED_VALUES_N50" ON public."SKEWED_VALUES" USING btree ("STRING_LIST_ID_EID");


--
-- Name: SORT_COLS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "SORT_COLS_N49" ON public."SORT_COLS" USING btree ("SD_ID");


--
-- Name: TABLECOLUMNPRIVILEGEINDEX; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "TABLECOLUMNPRIVILEGEINDEX" ON public."TBL_COL_PRIVS" USING btree ("AUTHORIZER", "TBL_ID", "COLUMN_NAME", "PRINCIPAL_NAME", "PRINCIPAL_TYPE", "TBL_COL_PRIV", "GRANTOR", "GRANTOR_TYPE");


--
-- Name: TABLEPRIVILEGEINDEX; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "TABLEPRIVILEGEINDEX" ON public."TBL_PRIVS" USING btree ("AUTHORIZER", "TBL_ID", "PRINCIPAL_NAME", "PRINCIPAL_TYPE", "TBL_PRIV", "GRANTOR", "GRANTOR_TYPE");


--
-- Name: TABLE_PARAMS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "TABLE_PARAMS_N49" ON public."TABLE_PARAMS" USING btree ("TBL_ID");


--
-- Name: TAB_COL_STATS_IDX; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "TAB_COL_STATS_IDX" ON public."TAB_COL_STATS" USING btree ("TBL_ID", "COLUMN_NAME");


--
-- Name: TBLS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "TBLS_N49" ON public."TBLS" USING btree ("DB_ID");


--
-- Name: TBLS_N50; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "TBLS_N50" ON public."TBLS" USING btree ("SD_ID");


--
-- Name: TBL_COL_PRIVS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "TBL_COL_PRIVS_N49" ON public."TBL_COL_PRIVS" USING btree ("TBL_ID");


--
-- Name: TBL_PRIVS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "TBL_PRIVS_N49" ON public."TBL_PRIVS" USING btree ("TBL_ID");


--
-- Name: TBL_TO_TXN_ID_IDX; Type: INDEX; Schema: public; Owner: hive
--

CREATE UNIQUE INDEX "TBL_TO_TXN_ID_IDX" ON public."TXN_TO_WRITE_ID" USING btree ("T2W_DATABASE", "T2W_TABLE", "T2W_TXNID");


--
-- Name: TBL_TO_WRITE_ID_IDX; Type: INDEX; Schema: public; Owner: hive
--

CREATE UNIQUE INDEX "TBL_TO_WRITE_ID_IDX" ON public."TXN_TO_WRITE_ID" USING btree ("T2W_DATABASE", "T2W_TABLE", "T2W_WRITEID");


--
-- Name: TYPE_FIELDS_N49; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX "TYPE_FIELDS_N49" ON public."TYPE_FIELDS" USING btree ("TYPE_NAME");


--
-- Name: UNIQUEDATABASE; Type: INDEX; Schema: public; Owner: hive
--

CREATE UNIQUE INDEX "UNIQUEDATABASE" ON public."DBS" USING btree ("NAME", "CTLG_NAME");


--
-- Name: UNIQUEFUNCTION; Type: INDEX; Schema: public; Owner: hive
--

CREATE UNIQUE INDEX "UNIQUEFUNCTION" ON public."FUNCS" USING btree ("FUNC_NAME", "DB_ID");


--
-- Name: UNIQUEPKG; Type: INDEX; Schema: public; Owner: hive
--

CREATE UNIQUE INDEX "UNIQUEPKG" ON public."PACKAGES" USING btree ("NAME", "DB_ID");


--
-- Name: UNIQUESCHEDULE; Type: INDEX; Schema: public; Owner: hive
--

CREATE UNIQUE INDEX "UNIQUESCHEDULE" ON public."SCHEDULED_QUERIES" USING btree ("SCHEDULE_NAME", "CLUSTER_NAMESPACE");


--
-- Name: UNIQUESTOREDPROC; Type: INDEX; Schema: public; Owner: hive
--

CREATE UNIQUE INDEX "UNIQUESTOREDPROC" ON public."STORED_PROCS" USING btree ("NAME", "DB_ID");


--
-- Name: UNIQUE_CATALOG; Type: INDEX; Schema: public; Owner: hive
--

CREATE UNIQUE INDEX "UNIQUE_CATALOG" ON public."CTLGS" USING btree ("NAME");


--
-- Name: completed_txn_components_index; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX completed_txn_components_index ON public."COMPLETED_TXN_COMPONENTS" USING btree ("CTC_DATABASE", "CTC_TABLE", "CTC_PARTITION");


--
-- Name: hl_txnid_index; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX hl_txnid_index ON public."HIVE_LOCKS" USING hash ("HL_TXNID");


--
-- Name: idx_scheduled_executions_last_update_time; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX idx_scheduled_executions_last_update_time ON public."SCHEDULED_EXECUTIONS" USING btree ("LAST_UPDATE_TIME");


--
-- Name: idx_scheduled_executions_scheduled_query_id; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX idx_scheduled_executions_scheduled_query_id ON public."SCHEDULED_EXECUTIONS" USING btree ("SCHEDULED_QUERY_ID");


--
-- Name: tc_txnid_index; Type: INDEX; Schema: public; Owner: hive
--

CREATE INDEX tc_txnid_index ON public."TXN_COMPONENTS" USING hash ("TC_TXNID");


--
-- Name: unique_scheduled_executions_id; Type: INDEX; Schema: public; Owner: hive
--

CREATE UNIQUE INDEX unique_scheduled_executions_id ON public."SCHEDULED_EXECUTIONS" USING btree ("SCHEDULED_EXECUTION_ID");


--
-- Name: BUCKETING_COLS BUCKETING_COLS_SD_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."BUCKETING_COLS"
    ADD CONSTRAINT "BUCKETING_COLS_SD_ID_fkey" FOREIGN KEY ("SD_ID") REFERENCES public."SDS"("SD_ID") DEFERRABLE;


--
-- Name: CATALOG_PARAMS CATALOG_PARAMS_FK1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."CATALOG_PARAMS"
    ADD CONSTRAINT "CATALOG_PARAMS_FK1" FOREIGN KEY ("CTLG_ID") REFERENCES public."CTLGS"("CTLG_ID") ON DELETE CASCADE;


--
-- Name: COLUMNS_V2 COLUMNS_V2_CD_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."COLUMNS_V2"
    ADD CONSTRAINT "COLUMNS_V2_CD_ID_fkey" FOREIGN KEY ("CD_ID") REFERENCES public."CDS"("CD_ID") DEFERRABLE;


--
-- Name: DATABASE_PARAMS DATABASE_PARAMS_DB_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."DATABASE_PARAMS"
    ADD CONSTRAINT "DATABASE_PARAMS_DB_ID_fkey" FOREIGN KEY ("DB_ID") REFERENCES public."DBS"("DB_ID") DEFERRABLE;


--
-- Name: DATACONNECTOR_PARAMS DATACONNECTOR_NAME_FK1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."DATACONNECTOR_PARAMS"
    ADD CONSTRAINT "DATACONNECTOR_NAME_FK1" FOREIGN KEY ("NAME") REFERENCES public."DATACONNECTORS"("NAME") ON DELETE CASCADE;


--
-- Name: DBS DBS_FK1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."DBS"
    ADD CONSTRAINT "DBS_FK1" FOREIGN KEY ("CTLG_NAME") REFERENCES public."CTLGS"("NAME");


--
-- Name: DB_PRIVS DB_PRIVS_DB_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."DB_PRIVS"
    ADD CONSTRAINT "DB_PRIVS_DB_ID_fkey" FOREIGN KEY ("DB_ID") REFERENCES public."DBS"("DB_ID") DEFERRABLE;


--
-- Name: DC_PRIVS DC_PRIVS_DC_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."DC_PRIVS"
    ADD CONSTRAINT "DC_PRIVS_DC_ID_fkey" FOREIGN KEY ("NAME") REFERENCES public."DATACONNECTORS"("NAME") DEFERRABLE;


--
-- Name: FUNCS FUNCS_FK1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."FUNCS"
    ADD CONSTRAINT "FUNCS_FK1" FOREIGN KEY ("DB_ID") REFERENCES public."DBS"("DB_ID") DEFERRABLE;


--
-- Name: FUNC_RU FUNC_RU_FK1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."FUNC_RU"
    ADD CONSTRAINT "FUNC_RU_FK1" FOREIGN KEY ("FUNC_ID") REFERENCES public."FUNCS"("FUNC_ID") DEFERRABLE;


--
-- Name: I_SCHEMA I_SCHEMA_DB_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."I_SCHEMA"
    ADD CONSTRAINT "I_SCHEMA_DB_ID_fkey" FOREIGN KEY ("DB_ID") REFERENCES public."DBS"("DB_ID");


--
-- Name: KEY_CONSTRAINTS KEY_CONSTRAINTS_FK1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."KEY_CONSTRAINTS"
    ADD CONSTRAINT "KEY_CONSTRAINTS_FK1" FOREIGN KEY ("PARENT_TBL_ID") REFERENCES public."TBLS"("TBL_ID") DEFERRABLE INITIALLY DEFERRED;


--
-- Name: KEY_CONSTRAINTS KEY_CONSTRAINTS_FK2; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."KEY_CONSTRAINTS"
    ADD CONSTRAINT "KEY_CONSTRAINTS_FK2" FOREIGN KEY ("CHILD_CD_ID") REFERENCES public."CDS"("CD_ID") DEFERRABLE INITIALLY DEFERRED;


--
-- Name: KEY_CONSTRAINTS KEY_CONSTRAINTS_FK3; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."KEY_CONSTRAINTS"
    ADD CONSTRAINT "KEY_CONSTRAINTS_FK3" FOREIGN KEY ("CHILD_TBL_ID") REFERENCES public."TBLS"("TBL_ID") DEFERRABLE INITIALLY DEFERRED;


--
-- Name: KEY_CONSTRAINTS KEY_CONSTRAINTS_FK4; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."KEY_CONSTRAINTS"
    ADD CONSTRAINT "KEY_CONSTRAINTS_FK4" FOREIGN KEY ("PARENT_CD_ID") REFERENCES public."CDS"("CD_ID") DEFERRABLE INITIALLY DEFERRED;


--
-- Name: MIN_HISTORY_WRITE_ID MIN_HISTORY_WRITE_ID_MH_TXNID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."MIN_HISTORY_WRITE_ID"
    ADD CONSTRAINT "MIN_HISTORY_WRITE_ID_MH_TXNID_fkey" FOREIGN KEY ("MH_TXNID") REFERENCES public."TXNS"("TXN_ID");


--
-- Name: MV_TABLES_USED MV_TABLES_USED_FK1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."MV_TABLES_USED"
    ADD CONSTRAINT "MV_TABLES_USED_FK1" FOREIGN KEY ("MV_CREATION_METADATA_ID") REFERENCES public."MV_CREATION_METADATA"("MV_CREATION_METADATA_ID") DEFERRABLE;


--
-- Name: MV_TABLES_USED MV_TABLES_USED_FK2; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."MV_TABLES_USED"
    ADD CONSTRAINT "MV_TABLES_USED_FK2" FOREIGN KEY ("TBL_ID") REFERENCES public."TBLS"("TBL_ID") DEFERRABLE;


--
-- Name: PACKAGES PACKAGES_FK1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PACKAGES"
    ADD CONSTRAINT "PACKAGES_FK1" FOREIGN KEY ("DB_ID") REFERENCES public."DBS"("DB_ID") DEFERRABLE;


--
-- Name: PARTITIONS PARTITIONS_SD_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PARTITIONS"
    ADD CONSTRAINT "PARTITIONS_SD_ID_fkey" FOREIGN KEY ("SD_ID") REFERENCES public."SDS"("SD_ID") DEFERRABLE;


--
-- Name: PARTITIONS PARTITIONS_TBL_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PARTITIONS"
    ADD CONSTRAINT "PARTITIONS_TBL_ID_fkey" FOREIGN KEY ("TBL_ID") REFERENCES public."TBLS"("TBL_ID") DEFERRABLE;


--
-- Name: PARTITION_KEYS PARTITION_KEYS_TBL_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PARTITION_KEYS"
    ADD CONSTRAINT "PARTITION_KEYS_TBL_ID_fkey" FOREIGN KEY ("TBL_ID") REFERENCES public."TBLS"("TBL_ID") DEFERRABLE;


--
-- Name: PARTITION_KEY_VALS PARTITION_KEY_VALS_PART_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PARTITION_KEY_VALS"
    ADD CONSTRAINT "PARTITION_KEY_VALS_PART_ID_fkey" FOREIGN KEY ("PART_ID") REFERENCES public."PARTITIONS"("PART_ID") DEFERRABLE;


--
-- Name: PARTITION_PARAMS PARTITION_PARAMS_PART_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PARTITION_PARAMS"
    ADD CONSTRAINT "PARTITION_PARAMS_PART_ID_fkey" FOREIGN KEY ("PART_ID") REFERENCES public."PARTITIONS"("PART_ID") DEFERRABLE;


--
-- Name: PART_COL_PRIVS PART_COL_PRIVS_PART_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PART_COL_PRIVS"
    ADD CONSTRAINT "PART_COL_PRIVS_PART_ID_fkey" FOREIGN KEY ("PART_ID") REFERENCES public."PARTITIONS"("PART_ID") DEFERRABLE;


--
-- Name: PART_COL_STATS PART_COL_STATS_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PART_COL_STATS"
    ADD CONSTRAINT "PART_COL_STATS_fkey" FOREIGN KEY ("PART_ID") REFERENCES public."PARTITIONS"("PART_ID") DEFERRABLE;


--
-- Name: PART_PRIVS PART_PRIVS_PART_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."PART_PRIVS"
    ADD CONSTRAINT "PART_PRIVS_PART_ID_fkey" FOREIGN KEY ("PART_ID") REFERENCES public."PARTITIONS"("PART_ID") DEFERRABLE;


--
-- Name: ROLE_MAP ROLE_MAP_ROLE_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."ROLE_MAP"
    ADD CONSTRAINT "ROLE_MAP_ROLE_ID_fkey" FOREIGN KEY ("ROLE_ID") REFERENCES public."ROLES"("ROLE_ID") DEFERRABLE;


--
-- Name: SCHEDULED_QUERIES SCHEDULED_EXECUTIONS_SCHQ_ACTIVE; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SCHEDULED_QUERIES"
    ADD CONSTRAINT "SCHEDULED_EXECUTIONS_SCHQ_ACTIVE" FOREIGN KEY ("ACTIVE_EXECUTION_ID") REFERENCES public."SCHEDULED_EXECUTIONS"("SCHEDULED_EXECUTION_ID") ON UPDATE RESTRICT ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;


--
-- Name: SCHEDULED_EXECUTIONS SCHEDULED_EXECUTIONS_SCHQ_FK; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SCHEDULED_EXECUTIONS"
    ADD CONSTRAINT "SCHEDULED_EXECUTIONS_SCHQ_FK" FOREIGN KEY ("SCHEDULED_QUERY_ID") REFERENCES public."SCHEDULED_QUERIES"("SCHEDULED_QUERY_ID") ON DELETE CASCADE;


--
-- Name: SCHEMA_VERSION SCHEMA_VERSION_CD_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SCHEMA_VERSION"
    ADD CONSTRAINT "SCHEMA_VERSION_CD_ID_fkey" FOREIGN KEY ("CD_ID") REFERENCES public."CDS"("CD_ID");


--
-- Name: SCHEMA_VERSION SCHEMA_VERSION_SCHEMA_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SCHEMA_VERSION"
    ADD CONSTRAINT "SCHEMA_VERSION_SCHEMA_ID_fkey" FOREIGN KEY ("SCHEMA_ID") REFERENCES public."I_SCHEMA"("SCHEMA_ID");


--
-- Name: SCHEMA_VERSION SCHEMA_VERSION_SERDE_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SCHEMA_VERSION"
    ADD CONSTRAINT "SCHEMA_VERSION_SERDE_ID_fkey" FOREIGN KEY ("SERDE_ID") REFERENCES public."SERDES"("SERDE_ID");


--
-- Name: SDS SDS_CD_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SDS"
    ADD CONSTRAINT "SDS_CD_ID_fkey" FOREIGN KEY ("CD_ID") REFERENCES public."CDS"("CD_ID") DEFERRABLE;


--
-- Name: SDS SDS_SERDE_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SDS"
    ADD CONSTRAINT "SDS_SERDE_ID_fkey" FOREIGN KEY ("SERDE_ID") REFERENCES public."SERDES"("SERDE_ID") DEFERRABLE;


--
-- Name: SD_PARAMS SD_PARAMS_SD_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SD_PARAMS"
    ADD CONSTRAINT "SD_PARAMS_SD_ID_fkey" FOREIGN KEY ("SD_ID") REFERENCES public."SDS"("SD_ID") DEFERRABLE;


--
-- Name: SERDE_PARAMS SERDE_PARAMS_SERDE_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SERDE_PARAMS"
    ADD CONSTRAINT "SERDE_PARAMS_SERDE_ID_fkey" FOREIGN KEY ("SERDE_ID") REFERENCES public."SERDES"("SERDE_ID") DEFERRABLE;


--
-- Name: SKEWED_COL_NAMES SKEWED_COL_NAMES_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SKEWED_COL_NAMES"
    ADD CONSTRAINT "SKEWED_COL_NAMES_fkey" FOREIGN KEY ("SD_ID") REFERENCES public."SDS"("SD_ID") DEFERRABLE;


--
-- Name: SKEWED_COL_VALUE_LOC_MAP SKEWED_COL_VALUE_LOC_MAP_fkey1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SKEWED_COL_VALUE_LOC_MAP"
    ADD CONSTRAINT "SKEWED_COL_VALUE_LOC_MAP_fkey1" FOREIGN KEY ("SD_ID") REFERENCES public."SDS"("SD_ID") DEFERRABLE;


--
-- Name: SKEWED_COL_VALUE_LOC_MAP SKEWED_COL_VALUE_LOC_MAP_fkey2; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SKEWED_COL_VALUE_LOC_MAP"
    ADD CONSTRAINT "SKEWED_COL_VALUE_LOC_MAP_fkey2" FOREIGN KEY ("STRING_LIST_ID_KID") REFERENCES public."SKEWED_STRING_LIST"("STRING_LIST_ID") DEFERRABLE;


--
-- Name: SKEWED_STRING_LIST_VALUES SKEWED_STRING_LIST_VALUES_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SKEWED_STRING_LIST_VALUES"
    ADD CONSTRAINT "SKEWED_STRING_LIST_VALUES_fkey" FOREIGN KEY ("STRING_LIST_ID") REFERENCES public."SKEWED_STRING_LIST"("STRING_LIST_ID") DEFERRABLE;


--
-- Name: SKEWED_VALUES SKEWED_VALUES_fkey1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SKEWED_VALUES"
    ADD CONSTRAINT "SKEWED_VALUES_fkey1" FOREIGN KEY ("STRING_LIST_ID_EID") REFERENCES public."SKEWED_STRING_LIST"("STRING_LIST_ID") DEFERRABLE;


--
-- Name: SKEWED_VALUES SKEWED_VALUES_fkey2; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SKEWED_VALUES"
    ADD CONSTRAINT "SKEWED_VALUES_fkey2" FOREIGN KEY ("SD_ID_OID") REFERENCES public."SDS"("SD_ID") DEFERRABLE;


--
-- Name: SORT_COLS SORT_COLS_SD_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."SORT_COLS"
    ADD CONSTRAINT "SORT_COLS_SD_ID_fkey" FOREIGN KEY ("SD_ID") REFERENCES public."SDS"("SD_ID") DEFERRABLE;


--
-- Name: STORED_PROCS STOREDPROC_FK1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."STORED_PROCS"
    ADD CONSTRAINT "STOREDPROC_FK1" FOREIGN KEY ("DB_ID") REFERENCES public."DBS"("DB_ID") DEFERRABLE;


--
-- Name: TABLE_PARAMS TABLE_PARAMS_TBL_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TABLE_PARAMS"
    ADD CONSTRAINT "TABLE_PARAMS_TBL_ID_fkey" FOREIGN KEY ("TBL_ID") REFERENCES public."TBLS"("TBL_ID") DEFERRABLE;


--
-- Name: TAB_COL_STATS TAB_COL_STATS_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TAB_COL_STATS"
    ADD CONSTRAINT "TAB_COL_STATS_fkey" FOREIGN KEY ("TBL_ID") REFERENCES public."TBLS"("TBL_ID") DEFERRABLE;


--
-- Name: TBLS TBLS_DB_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TBLS"
    ADD CONSTRAINT "TBLS_DB_ID_fkey" FOREIGN KEY ("DB_ID") REFERENCES public."DBS"("DB_ID") DEFERRABLE;


--
-- Name: TBLS TBLS_SD_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TBLS"
    ADD CONSTRAINT "TBLS_SD_ID_fkey" FOREIGN KEY ("SD_ID") REFERENCES public."SDS"("SD_ID") DEFERRABLE;


--
-- Name: TBL_COL_PRIVS TBL_COL_PRIVS_TBL_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TBL_COL_PRIVS"
    ADD CONSTRAINT "TBL_COL_PRIVS_TBL_ID_fkey" FOREIGN KEY ("TBL_ID") REFERENCES public."TBLS"("TBL_ID") DEFERRABLE;


--
-- Name: TBL_PRIVS TBL_PRIVS_TBL_ID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TBL_PRIVS"
    ADD CONSTRAINT "TBL_PRIVS_TBL_ID_fkey" FOREIGN KEY ("TBL_ID") REFERENCES public."TBLS"("TBL_ID") DEFERRABLE;


--
-- Name: TXN_COMPONENTS TXN_COMPONENTS_TC_TXNID_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TXN_COMPONENTS"
    ADD CONSTRAINT "TXN_COMPONENTS_TC_TXNID_fkey" FOREIGN KEY ("TC_TXNID") REFERENCES public."TXNS"("TXN_ID");


--
-- Name: TYPE_FIELDS TYPE_FIELDS_TYPE_NAME_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."TYPE_FIELDS"
    ADD CONSTRAINT "TYPE_FIELDS_TYPE_NAME_fkey" FOREIGN KEY ("TYPE_NAME") REFERENCES public."TYPES"("TYPES_ID") DEFERRABLE;


--
-- Name: WM_MAPPING WM_MAPPING_FK1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_MAPPING"
    ADD CONSTRAINT "WM_MAPPING_FK1" FOREIGN KEY ("RP_ID") REFERENCES public."WM_RESOURCEPLAN"("RP_ID") DEFERRABLE;


--
-- Name: WM_MAPPING WM_MAPPING_FK2; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_MAPPING"
    ADD CONSTRAINT "WM_MAPPING_FK2" FOREIGN KEY ("POOL_ID") REFERENCES public."WM_POOL"("POOL_ID") DEFERRABLE;


--
-- Name: WM_POOL WM_POOL_FK1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_POOL"
    ADD CONSTRAINT "WM_POOL_FK1" FOREIGN KEY ("RP_ID") REFERENCES public."WM_RESOURCEPLAN"("RP_ID") DEFERRABLE;


--
-- Name: WM_POOL_TO_TRIGGER WM_POOL_TO_TRIGGER_FK1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_POOL_TO_TRIGGER"
    ADD CONSTRAINT "WM_POOL_TO_TRIGGER_FK1" FOREIGN KEY ("POOL_ID") REFERENCES public."WM_POOL"("POOL_ID") DEFERRABLE;


--
-- Name: WM_POOL_TO_TRIGGER WM_POOL_TO_TRIGGER_FK2; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_POOL_TO_TRIGGER"
    ADD CONSTRAINT "WM_POOL_TO_TRIGGER_FK2" FOREIGN KEY ("TRIGGER_ID") REFERENCES public."WM_TRIGGER"("TRIGGER_ID") DEFERRABLE;


--
-- Name: WM_RESOURCEPLAN WM_RESOURCEPLAN_FK1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_RESOURCEPLAN"
    ADD CONSTRAINT "WM_RESOURCEPLAN_FK1" FOREIGN KEY ("DEFAULT_POOL_ID") REFERENCES public."WM_POOL"("POOL_ID") DEFERRABLE;


--
-- Name: WM_TRIGGER WM_TRIGGER_FK1; Type: FK CONSTRAINT; Schema: public; Owner: hive
--

ALTER TABLE ONLY public."WM_TRIGGER"
    ADD CONSTRAINT "WM_TRIGGER_FK1" FOREIGN KEY ("RP_ID") REFERENCES public."WM_RESOURCEPLAN"("RP_ID") DEFERRABLE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: hive
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

\unrestrict b4v5cAgVdqw59ecKZz4KJFvhxtRLP8aeWcPfbJdO6IWfdPbOF8SOI4ltSI0bcec

