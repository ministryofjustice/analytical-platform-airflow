from datetime import datetime
from airflow.models import DAG
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator
from airflow.providers.slack.notifications.slack import send_slack_notification
from airflow.providers.cncf.kubernetes.secret import (
    Secret,
)

REPOSITORY_NAME="PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG="PLACEHOLDER_REPOSITORY_TAG"
PROJECT="PLACEHOLDER_PROJECT"
WORKFLOW="PLACEHOLDER_WORKFLOW"
ENVIRONMENT="PLACEHOLDER_ENVIRONMENT"
OWNER="PLACEHOLDER_OWNER"

# DELTA_FETCH_SIZE = "100000"
# RM_FETCH_SIZE = "300000"

# Increase fetch sizes by a factor of 20, because breaking the AP is fun...
DELTA_FETCH_SIZE = "2000000"
RM_FETCH_SIZE = "6000000"

# NOMIS CONSTANTS:
# A dictionary specifying irregular PK extractions
# and a list of days of month on which they are extracted
# (for prohibitvely large tables)
PK_EXCEPTIONS = {"11": [0]}
PK_EXTRACTIONS = {
    "1": ["OFFENDER_PROFILE_DETAILS"],
    "2": ["ORDERS", "OFFENDER_EXTERNAL_MOVEMENTS"],
    "3": ["OFFENDER_SENTENCE_CHARGES", "INCIDENT_CASE_RESPONSES"],
    "4": ["OFFENDER_ASSESSMENTS", "INCIDENT_CASE_QUESTIONS"],
    "5": ["ADDRESSES", "BED_ASSIGNMENT_HISTORIES"],
    "6": ["COURT_EVENT_CHARGES", "OFFENDER_ASSESSMENT_ITEMS"],
    "7": ["INCIDENT_CASE_PARTIES", "OFFENDER_SENTENCES", "PERSONS", "OFFENDER_VISITS"],
    "8": [
        "OFFENDER_BOOKINGS",
        "OFFENDER_SENT_CALCULATIONS",
        "COURT_EVENTS",
        "OFFENDER_CONTACT_PERSONS",
    ],
    "9": [
        "OFFENDER_ALERTS",
        "OFFENDER_SENTENCE_TERMS",
        "OFFENDER_IMPRISON_STATUSES",
        "OFFENDER_IEP_LEVELS",
    ],
    "10": [
        "OFFENDER_VISIT_VISITORS",
        "OFFENDER_PHYSICAL_ATTRIBUTES",
        "OFFENDER_CSIP_ATTENDEES",
        "OFFENDER_CSIP_FACTORS",
        "OFFENDER_CSIP_INTVW",
        "OFFENDER_CSIP_PLANS",
        "OFFENDER_CSIP_REPORTS",
        "OFFENDER_CSIP_REVIEWS",
    ],
    "11": ["OFFENDER_TRANSACTIONS"],
    "12": [
        "AGENCY_VISIT_TIMES",
        "OFFENDER_VISIT_ORDERS",
        "OFFENDER_RESTRICTIONS",
        "AGENCY_VISIT_SLOTS",
        "CORPORATES",
        "USER_ACCESSIBLE_CASELOADS",
        "CASELOAD_AGENCY_LOCATIONS",
        "OFFENDER_IND_SCHEDULES",
        "OFFENDER_VO_VISITORS",
    ],
    "0": [
        "OFFENDERS",
        "OFFENDER_CHARGES",
        "INCIDENT_CASES",
        "ADDRESS_USAGES",
        "OFFENDER_OIC_SANCTIONS",
        "OFFENDER_CASES",
        "OFFENDER_HEALTH_PROBLEMS",
        "OFFENDER_IDENTIFIERS",
        "OFFENDER_RELEASE_DETAILS",
        "OFFENDER_REHAB_DECISIONS",
        "AGENCY_INTERNAL_LOCATIONS",
        "OFFENDER_NA_DETAILS",
        "OFFENDER_NON_ASSOCIATIONS",
        "REFERENCE_CODES",
        "AGENCY_LOCATIONS",
        "PROFILE_CODES",
        "QUESTIONNAIRE_QUESTIONS",
        "QUESTIONNAIRE_ANSWERS",
        "QUESTIONNAIRES",
        "IMPRISONMENT_STATUSES",
        "INCIDENT_STATUSES",
        "OFFENCES",
        "QUESTIONNAIRE_ROLES",
        "ASSESSMENTS",
        "STATUTES",
        "MOVEMENT_REASONS",
        "OFFENCE_INDICATORS",
        "OFFENCE_RESULT_CODES",
        "AREAS",
        "OFFENDER_RISK_PREDICTORS",
        "GANG_NON_ASSOCIATIONS",
        "GANGS",
        "OFFENDER_GANG_AFFILIATIONS",
        "OFFENDER_GANG_EVIDENCES",
        "OFFENDER_GANG_INVESTS",
        "OFFENDER_PERSON_RESTRICTS",
        "STAFF_MEMBERS",
        "RANDOM_TESTING_PROGRAMS",
        "REHABILITATION_PROVIDERS",
        "OFFENDER_REHAB_PROVIDERS",
        "SENTENCE_CALC_TYPES",
        "PHONES",
        "INTERNET_ADDRESSES",
        "STAFF_USER_ACCOUNTS",
        "PROFILE_TYPES",
    ],
}

nomis_secret_1=[Secret(
        deploy_type="env",
        deploy_target="SECRET_DB_PWD",
        secret=f"{PROJECT}-{WORKFLOW}-db-pwd",
        key="data"
    )
]
nomis_secret_2=[Secret(
        deploy_type="env",
        deploy_target="SECRET_DB_USER_ID",
        secret=f"{PROJECT}-{WORKFLOW}-db-user-id",
        key="data"
    )
]
nomis_secret_3=[Secret(
        deploy_type="env",
        deploy_target="SECRET_DB_IP",
        secret=f"{PROJECT}-{WORKFLOW}-db-ip",
        key="data"
    )
]
nomis_secret_4=[Secret(
        deploy_type="env",
        deploy_target="SECRET_DB_PORT",
        secret=f"{PROJECT}-{WORKFLOW}-db-port",
        key="data"
    )
]
nomis_secret_5=[Secret(
        deploy_type="env",
        deploy_target="SECRET_DB_SERVICE_NAME",
        secret=f"{PROJECT}-{WORKFLOW}-db-service-name",
        key="data"
    )
]

task_args = {
    "compute_profile": "general-on-demand-1vcpu-4gb",
    "image": f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    "name": "nomis_extraction",
    "environment": ENVIRONMENT,
    "project": PROJECT,
    "workflow": WORKFLOW,
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": 300,
}

dag = DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=task_args,
    description="Extract data from the NOMIS T62 Database",
    start_date=datetime(2025, 11, 1),
    schedule="00 01 * * *",
    catchup=False,
)

tasks = {}

tasks["initialise-dag"] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id="initialise-dag",
    env_vars={
        "PYTHON_SCRIPT_NAME": "initialise_dag.py",
        "NOMIS_T62_FETCH_SIZE": DELTA_FETCH_SIZE,
        "DAG_ID": dag.dag_id,
#        "ENV": "PRODUCTION",
        "ENV": "DEVELOPMENT",
        "DAG_RUN_UTC_UNIXTIME": str(int(datetime.utcnow().timestamp())),
    },
)


tasks["nomis-delta-extract"] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id="nomis-delta-extract",
    secrets=[nomis_secret_1, nomis_secret_2, nomis_secret_3, nomis_secret_4, nomis_secret_5],
    env_vars={
        "PYTHON_SCRIPT_NAME": "nomis_delta_extract.py",
        "NOMIS_T62_FETCH_SIZE": DELTA_FETCH_SIZE,
        "DAG_ID": dag.dag_id,
 #       "ENV": "PRODUCTION",
        "ENV": "DEVELOPMENT",
    },

)

tasks["nomis-delta-extract-check"] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id="nomis-delta-extract-check",
    secrets=[nomis_secret_1, nomis_secret_2, nomis_secret_3, nomis_secret_4, nomis_secret_5],
    env_vars={
        "PYTHON_SCRIPT_NAME": "test_extraction_outputs_and_move_to_raw.py",
        "NOMIS_T62_FETCH_SIZE": DELTA_FETCH_SIZE,
        "DAG_ID": dag.dag_id,
  #      "ENV": "PRODUCTION",
        "ENV": "DEVELOPMENT",
    },

)

# Set dependencies
(
    tasks["nomis-delta-extract"]
    >> tasks["nomis-delta-extract-check"]
    >> tasks["initialise-dag"]
)

# Deletes
#for i, L in PK_EXTRACTIONS.items():
#    if i in PK_EXCEPTIONS and datetime.now().day not in PK_EXCEPTIONS[i]:
#        continue
#    tables_string = ",".join(L)
#   tasks[f"nomis-pk-deletes-extracts-{i}"] = AnalyticalPlatformStandardOperator(
tasks["nomis-pk-deletes-extract"] = AnalyticalPlatformStandardOperator(
    dag=dag,
#   task_id=f"nomis-pk-deletes-extracts-{i}",
    task_id="nomis-pk-deletes-extract",
    secrets=[nomis_secret_1, nomis_secret_2, nomis_secret_3, nomis_secret_4, nomis_secret_5],
    env_vars={
#        "PK_EXTRACT_TABLES": tables_string,
        "PYTHON_SCRIPT_NAME": "nomis_deletes_extract.py",
        "NOMIS_T62_FETCH_SIZE": RM_FETCH_SIZE,
        "AWS_METADATA_SERVICE_TIMEOUT": "60",
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
        "DAG_ID": dag.dag_id,
   #    "ENV": "PRODUCTION",
        "ENV": "DEVELOPMENT",
    },

)

#   tasks[f"nomis-pk-deletes-extract-check-{i}"] = AnalyticalPlatformStandardOperator(
tasks["nomis-pk-deletes-extract-check"] = AnalyticalPlatformStandardOperator(
    dag=dag,
#   task_id=f"nomis-pk-deletes-extract-check-{i}",
    task_id="nomis-pk-deletes-extract-check",
    secrets=[nomis_secret_1, nomis_secret_2, nomis_secret_3, nomis_secret_4, nomis_secret_5],
    env_vars={
#        "PK_EXTRACT_TABLES": tables_string,
        "PYTHON_SCRIPT_NAME": "test_deletes_extraction_outputs_and_move_to_raw.py",
        "NOMIS_T62_FETCH_SIZE": RM_FETCH_SIZE,
        "AWS_METADATA_SERVICE_TIMEOUT": "60",
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
        "DAG_ID": dag.dag_id,
    #   "ENV": "PRODUCTION",
        "ENV": "DEVELOPMENT",
    },

)

(
    tasks["nomis-pk-deletes-extract"]
    >> tasks["nomis-pk-deletes-extract-check"]
#   tasks[f"nomis-pk-deletes-extract-{i}"]
#   >> tasks[f"nomis-pk-deletes-extract-check-{i}"]
    >> tasks["initialise-dag"]

)
