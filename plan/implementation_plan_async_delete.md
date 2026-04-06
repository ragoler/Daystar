# Implementation Plan - Asynchronous Cluster Deletion and Fast Cleanup

This plan outlines changes to make cluster deletion asynchronous, which will fix the issue where startup cleanup blocks on the first cluster it tries to delete.

## Goal
Make `delete_cluster` non-blocking to allow fast cleanup of multiple clusters on startup and fluid UI updates, fulfilling the user's request to use async behavior for all GKE APIs.

## Proposed Changes

### Backend

#### [Modify] [gke_prober.py](file:///Users/ragoler/Documents/JetSki/Daystar/backend/gke_prober.py)
- In `_delete_cluster` function, remove the call to `_wait_for_operation` and return `True` immediately after triggering the deletion operation.
- This will allow `cleanup_old_resources` to loop through all old clusters and trigger deletion for all of them quickly without waiting 10 minutes for each.

```python
        try:
            operation = self.client.delete_cluster(name=name)
            self.logs += f"Cluster deletion operation started: {operation.name}\n"
            
            response_data = MessageToDict(operation._pb) if MessageToDict and hasattr(operation, '_pb') else str(operation)
            log_api_call(cluster_name, "delete_cluster", request_data, response_data)
            
            # Remove this line:
            # return self._wait_for_operation(cluster_name, operation.name)
            return True
```

## Verification Plan

### Manual Verification
- Run the application with multiple old clusters labeled `daystar` existing in GKE.
- Verify that `gcloud container clusters list` shows all of them transitioning to `STOPPING` state quickly after startup.
