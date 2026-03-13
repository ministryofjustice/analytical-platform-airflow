from datetime import datetime, timedelta

from airflow.models import DAG
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator

REPOSITORY_NAME="PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG="PLACEHOLDER_REPOSITORY_TAG"
PROJECT="PLACEHOLDER_PROJECT"
WORKFLOW="PLACEHOLDER_WORKFLOW"
ENVIRONMENT="PLACEHOLDER_ENVIRONMENT"
OWNER="PLACEHOLDER_OWNER"

IMAGE = f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}"
SNAPSHOT_DATE = "{{ (data_interval_end - macros.timedelta(hours=20)).strftime('%Y-%m-%d') }}"
GLUE_ROLE = "airflow_prod_data_linking"
VERSION = "prod"

default_args = {
    "depends_on_past": False,
    "email_on_failure": True,
    "owner": OWNER,
    "retries": 4,
    "retry_delay": timedelta(seconds=60),
    "retry_exponential_backoff": False,
}

dag = DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=default_args,
    description=(
        "Weekly data linking, pushing updates to just_link "
        "https://data-discovery-tool.analytical-platform.service.justice.gov.uk/just_link/index.html"
    ),
    start_date=datetime(2024, 5, 19),
    schedule="0 20 * * 7",
    catchup=False,
    max_active_runs=1,
)


def make_task(task_id: str, job_path: str, compute_profile: str) -> AnalyticalPlatformStandardOperator:
    return AnalyticalPlatformStandardOperator(
        dag=dag,
        task_id=task_id.replace("_", "-"),
        name=f"{PROJECT}.{WORKFLOW}.{task_id.replace('_', '-')}",
        compute_profile=compute_profile,
        image=IMAGE,
        environment=f"{ENVIRONMENT}",
        project=f"{PROJECT}",
        workflow=f"{WORKFLOW}",
        env_vars={
            "JOB_PATH": job_path,
            "SNAPSHOT_DATE": SNAPSHOT_DATE,
            "GLUE_ROLE": GLUE_ROLE,
            "VERSION": VERSION,
        },
    )


tasks = {
    "config": make_task("config", "07_other_glue_jobs/get_closest_snapshot_dates", "general-spot-1vcpu-4gb"),
    "update_s3_logs": make_task("update_s3_logs", "07_other_glue_jobs/update_s3_logs", "general-spot-1vcpu-4gb"),
    "product_monitoring": make_task("product_monitoring", "07_other_glue_jobs/product_monitoring", "general-spot-1vcpu-4gb"),
    "mh_src_n": make_task("mh_src_n", "01_node_generation/source_nodes/person/mags_hocas", "general-spot-1vcpu-4gb"),
    "mh_std_n": make_task("mh_std_n", "01_node_generation/standardised_nodes/person/mags_hocas", "general-spot-8vcpu-32gb"),
    "mh_e": make_task("mh_e", "03_edge_generation/person/mags_hocas", "general-spot-16vcpu-64gb"),
    "cx_src_n": make_task("cx_src_n", "01_node_generation/source_nodes/person/crown_xhibit", "general-spot-1vcpu-4gb"),
    "cx_std_n": make_task("cx_std_n", "01_node_generation/standardised_nodes/person/crown_xhibit", "general-spot-8vcpu-32gb"),
    "cx_e": make_task("cx_e", "03_edge_generation/person/crown_xhibit", "general-spot-16vcpu-64gb"),
    "cp_src_n": make_task("cp_src_n", "01_node_generation/source_nodes/person/common_platform", "general-spot-1vcpu-4gb"),
    "cp_std_n": make_task("cp_std_n", "01_node_generation/standardised_nodes/person/common_platform", "general-spot-8vcpu-32gb"),
    "cp_e": make_task("cp_e", "03_edge_generation/person/common_platform", "general-spot-16vcpu-64gb"),
    "pn_src_n": make_task("pn_src_n", "01_node_generation/source_nodes/person/prison_nomis", "general-spot-1vcpu-4gb"),
    "pn_std_n": make_task("pn_std_n", "01_node_generation/standardised_nodes/person/prison_nomis", "general-spot-8vcpu-32gb"),
    "pn_e": make_task("pn_e", "03_edge_generation/person/prison_nomis", "general-spot-16vcpu-64gb"),
    "po_src_n": make_task("po_src_n", "01_node_generation/source_nodes/person/prison_oasys", "general-spot-1vcpu-4gb"),
    "po_std_n": make_task("po_std_n", "01_node_generation/standardised_nodes/person/prison_oasys", "general-spot-8vcpu-32gb"),
    "po_e": make_task("po_e", "03_edge_generation/person/prison_oasys", "general-spot-16vcpu-64gb"),
    "pd_src_n": make_task("pd_src_n", "01_node_generation/source_nodes/person/probation_delius", "general-spot-1vcpu-4gb"),
    "pd_std_n": make_task("pd_std_n", "01_node_generation/standardised_nodes/person/probation_delius", "general-spot-8vcpu-32gb"),
    "pd_e": make_task("pd_e", "03_edge_generation/person/probation_delius", "general-spot-16vcpu-64gb"),
    "fm_src_n": make_task("fm_src_n", "01_node_generation/source_nodes/person/familyman", "general-spot-1vcpu-4gb"),
    "fm_std_n": make_task("fm_std_n", "01_node_generation/standardised_nodes/person/familyman", "general-spot-8vcpu-32gb"),
    "fm_e": make_task("fm_e", "03_edge_generation/person/familyman", "general-spot-16vcpu-64gb"),
    "ccp_src_n": make_task("ccp_src_n", "01_node_generation/source_nodes/person/civil_caseman_pcol", "general-spot-1vcpu-4gb"),
    "ccp_std_n": make_task("ccp_std_n", "01_node_generation/standardised_nodes/person/civil_caseman_pcol", "general-spot-8vcpu-32gb"),
    "ccp_e": make_task("ccp_e", "03_edge_generation/person/civil_caseman_pcol", "general-spot-16vcpu-64gb"),
    "cjs_std_n": make_task("cjs_std_n", "01_node_generation/standardised_nodes/person/cjs", "general-spot-32vcpu-128gb"),
    "cjs_e": make_task("cjs_e", "03_edge_generation/person/cjs", "general-spot-32vcpu-128gb"),
    "cjs_cl": make_task("cjs_cl", "04_cluster_generation/person/cjs", "general-spot-32vcpu-128gb"),
    "prod_int_cjs": make_task("prod_int_cjs", "06_products/internal/person/cjs", "general-spot-8vcpu-32gb"),
    "xjs_std_n": make_task("xjs_std_n", "01_node_generation/standardised_nodes/person/xjs", "general-spot-32vcpu-128gb"),
    "xjs_e": make_task("xjs_e", "03_edge_generation/person/xjs", "general-spot-32vcpu-128gb"),
    "xjs_cl": make_task("xjs_cl", "04_cluster_generation/person/xjs", "general-spot-32vcpu-128gb"),
    "prod_int_xjs": make_task("prod_int_xjs", "06_products/internal/person/xjs", "general-spot-8vcpu-32gb"),
    "j_cx_src_n": make_task("j_cx_src_n", "01_node_generation/source_nodes/journey/crown_xhibit", "general-spot-1vcpu-4gb"),
    "j_std_n": make_task("j_std_n", "01_node_generation/standardised_nodes/journey/mh-cx", "general-spot-16vcpu-64gb"),
    "j_e": make_task("j_e", "03_edge_generation/journey/mh-cx", "general-spot-16vcpu-64gb"),
    "prod_int_j": make_task("prod_int_j", "06_products/internal/journey/mh-cx", "general-spot-8vcpu-32gb"),
}

for source in [
    "mh_src_n",
    "cx_src_n",
    "cp_src_n",
    "pn_src_n",
    "po_src_n",
    "pd_src_n",
    "fm_src_n",
    "ccp_src_n",
    "j_cx_src_n",
]:
    tasks["config"] >> tasks[source]

for chain in [
    ["mh_src_n", "mh_std_n", "mh_e"],
    ["cx_src_n", "cx_std_n", "cx_e"],
    ["cp_src_n", "cp_std_n", "cp_e"],
    ["pn_src_n", "pn_std_n", "pn_e"],
    ["po_src_n", "po_std_n", "po_e"],
    ["pd_src_n", "pd_std_n", "pd_e"],
    ["fm_src_n", "fm_std_n", "fm_e"],
    ["ccp_src_n", "ccp_std_n", "ccp_e"],
    ["cjs_std_n", "cjs_e", "cjs_cl", "prod_int_cjs"],
    ["xjs_std_n", "xjs_e", "xjs_cl", "prod_int_xjs"],
    ["j_cx_src_n", "j_std_n", "j_e", "prod_int_j"],
]:
    for upstream, downstream in zip(chain, chain[1:]):
        tasks[upstream] >> tasks[downstream]

for upstream in ["mh_std_n", "cx_std_n", "cp_std_n", "pn_std_n", "po_std_n", "pd_std_n"]:
    tasks[upstream] >> tasks["cjs_std_n"]

for upstream in ["cjs_std_n", "fm_std_n", "ccp_std_n"]:
    tasks[upstream] >> tasks["xjs_std_n"]

for upstream in ["mh_e", "cx_e", "cp_e", "pn_e", "po_e", "pd_e", "cjs_e"]:
    tasks[upstream] >> tasks["cjs_cl"]

for upstream in ["mh_e", "cx_e", "cp_e", "pn_e", "po_e", "pd_e", "fm_e", "ccp_e", "cjs_e", "xjs_e"]:
    tasks[upstream] >> tasks["xjs_cl"]

tasks["mh_src_n"] >> tasks["j_std_n"]
tasks["cjs_cl"] >> tasks["j_std_n"]
tasks["prod_int_cjs"] >> tasks["product_monitoring"]
