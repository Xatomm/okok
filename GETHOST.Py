from google.cloud import compute_v1


def get_hostname(project_id: str, zone: str, instance_name: str) -> str:
    """
    Retrieve the hostname of given instance.

    Args:
        project_id: project ID or project number of the Cloud project you want to use.
        zone: name of the zone you want to use. For example: "us-west3-b"
        instance_name: name of the virtual machine to check.

    Returns:
        The hostname of an instance.
    """
    instance_client = compute_v1.InstancesClient()
    instance = instance_client.get(
        project=project_id, zone=zone, instance=instance_name
    )
    return instance.hostname