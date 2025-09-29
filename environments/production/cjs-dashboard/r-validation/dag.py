from datetime import datetime
from functools import partial
from airflow.models import DAG
from airflow.operators.email import EmailOperator
from airflow.operators.python import get_current_context
from airflow.operators.python_operator import PythonOperator
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator

REPOSITORY_NAME="PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG="PLACEHOLDER_REPOSITORY_TAG"
PROJECT="PLACEHOLDER_PROJECT"
WORKFLOW="PLACEHOLDER_WORKFLOW"
ENVIRONMENT="PLACEHOLDER_ENVIRONMENT"
OWNER="PLACEHOLDER_OWNER"
EXECUTION_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

data_providers = [
  "ho",
  "cps",
  "moj",
  "hmcts"
]

default_args = {
  "depends_on_past": False,
  "email_on_failure": False,
  "owner": f"{OWNER}",
  "retries": 2,
  "retry_delay": 60,
}

dag = DAG(
  dag_id=f"{PROJECT}.{WORKFLOW}",
  default_args=default_args,
  start_date=datetime(2025, 9, 19),
  end_date=datetime(2025, 10, 24),
  schedule="*/30 9-17 * * 1-5",
)

# Define function to handle email operator, uses xcom to pull timestamp information
# from r validation process in task 1 (below)
def _send_email(data_provider):
    context = get_current_context()
    returned = context.get('task_instance')\
                      .xcom_pull(task_ids=f'r-validation-{data_provider}')
    max_timestamp = returned["max_timestamp"]
    result = returned["overall_result"]
    task_id = f"send-email-{data_provider}"
    email_addresses = ["joe.dods@justice.gov.uk",
                       "rolake.odebunmi@justice.gov.uk"]
    subject = f"New data validation output ready - {data_provider.upper()} - {result}"
    # HTML contents of email
    email_contents = ("<h3>A new data validation output has been created</h3>"
                      f"Data provider: {data_provider.upper()}<br>"
                      f"Extraction max_timestamp: {max_timestamp}<br>"
                      f"Result: {result}"
                      "<p>Detailed results saved in "
                      f"s3://alpha-cjs-scorecard/data_validation/prod/{data_provider}/{max_timestamp}/</p>"
                      )
    email_task = EmailOperator(
        to=email_addresses,
        subject=subject,
        html_content=email_contents,
        dag=dag,
        task_id=task_id
    )
    return email_task.execute(context=context)

def send_email(data_provider):
    return partial(_send_email, data_provider)

# Runs tasks for data providers simultaneously
for data_provider in data_providers:
  # Environmental variables for passing to the docker container
  env_vars = {
        "DATA_PROVIDER": data_provider,
        "ENVIRONMENT": ENVIRONMENT,
        "EXECUTION_TIME": EXECUTION_TIME,
        "AWS_METADATA_SERVICE_TIMEOUT": "60",
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5"
    }

  task_id_1 = f"r-validation-{data_provider}"
  task_1 = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id=task_id_1,
    name=f"{PROJECT}.{WORKFLOW}",
    compute_profile="general-spot-1vcpu-4gb",
    image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    env_vars=env_vars,
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    do_xcom_push=True
  )

  # If Task 1 succeeds, Task 2 will call the send_email function
  email_func = send_email(data_provider)
  task_id_2 = f"python-send-email-{data_provider}"
  task_2 = PythonOperator(
    dag=dag,
    task_id=task_id_2,
    python_callable=email_func,
    provide_context=True
  )

  task_1 >> task_2
