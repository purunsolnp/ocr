def blob_callback(blob, metadata):
    blobs_to_remove = {
        "0fcd5a3c65fee6a9681baf601b0190ad33e59bb6",
        "2bf7dbbf82a89127735ad91406970db2317fa290"
    }
    if metadata.original_id.hex in blobs_to_remove:
        return None
    return blob
