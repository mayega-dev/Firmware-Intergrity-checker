#include "crypto.h"
#include "firmware_config.h"
#include "mbedtls/sha256.h"
#include <esp_flash.h>
#include <esp_log.h>
#include <esp_partition.h>
#include <nvs.h>
#include <stdlib.h>
#include <stdio.h>

static const char *TAG = "CRYPTO";

esp_err_t crypto_calculate_partition_hash(const char *partition_label, uint8_t *output_hash) {
    // NOTE: ESP_PARTITION_SUBTYPE_ANY will match the first APP partition
    // with this label. If your partition table defines multiple entries
    // sharing a label across subtypes, pin an explicit subtype instead so
    // this can't silently hash the wrong image.
    const esp_partition_t *partition =
        esp_partition_find_first(ESP_PARTITION_TYPE_APP, ESP_PARTITION_SUBTYPE_ANY, partition_label);
    if (partition == NULL) {
        ESP_LOGE(TAG, "Partition '%s' not found", partition_label);
        return ESP_ERR_NOT_FOUND;
    }

    // Allocate a buffer to read chunks of flash memory dynamically
    size_t chunk_size = 4096;
    uint8_t *buffer = malloc(chunk_size);
    if (!buffer) {
        return ESP_ERR_NO_MEM;
    }

    mbedtls_sha256_context ctx;
    mbedtls_sha256_init(&ctx);
    mbedtls_sha256_starts(&ctx, 0); // 0 for SHA-256

    size_t offset = 0;
    size_t size_to_read = partition->size;
    esp_err_t err = ESP_OK;

    while (size_to_read > 0) {
        size_t read_len = (size_to_read > chunk_size) ? chunk_size : size_to_read;
        err = esp_partition_read(partition, offset, buffer, read_len);
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Flash read failed at offset 0x%x", offset);
            break;
        }

        mbedtls_sha256_update(&ctx, buffer, read_len);
        offset += read_len;
        size_to_read -= read_len;
    }

    mbedtls_sha256_finish(&ctx, output_hash);
    mbedtls_sha256_free(&ctx);
    free(buffer);

    return err;
}

void crypto_hash_to_str(const uint8_t *hash, char *out_str) {
    for (int i = 0; i < HASH_SIZE_BYTES; i++) {
        sprintf(&out_str[i * 2], "%02x", hash[i]);
    }
    out_str[HASH_SIZE_BYTES * 2] = '\0';
}

bool crypto_load_reference_hash(uint8_t *out_hash) {
    nvs_handle_t handle;
    esp_err_t err = nvs_open(REFHASH_NVS_NAMESPACE, NVS_READONLY, &handle);
    if (err != ESP_OK) {
        return false; // Not provisioned yet - caller should fall back to a self-established baseline.
    }

    size_t len = HASH_SIZE_BYTES;
    err = nvs_get_blob(handle, REFHASH_NVS_KEY, out_hash, &len);
    nvs_close(handle);

    if (err != ESP_OK || len != HASH_SIZE_BYTES) {
        return false;
    }
    return true;
}

esp_err_t crypto_store_reference_hash(const uint8_t *hash) {
    nvs_handle_t handle;
    esp_err_t err = nvs_open(REFHASH_NVS_NAMESPACE, NVS_READWRITE, &handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to open reference-hash NVS namespace (0x%x)", err);
        return err;
    }

    err = nvs_set_blob(handle, REFHASH_NVS_KEY, hash, HASH_SIZE_BYTES);
    if (err == ESP_OK) {
        err = nvs_commit(handle);
    }
    nvs_close(handle);
    return err;
}
