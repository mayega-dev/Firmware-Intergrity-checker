#ifndef CRYPTO_H
#define CRYPTO_H

#include <esp_err.h>
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#define HASH_SIZE_BYTES 32 // SHA-256 outputs 32 bytes

/**
 * @brief Computes the SHA-256 hash of a specific memory partition.
 * @param partition_label Label of the partition to hash (e.g., "factory")
 * @param output_hash Buffer to store the calculated 32-byte hash
 * @return esp_err_t ESP_OK on success
 */
esp_err_t crypto_calculate_partition_hash(const char *partition_label, uint8_t *output_hash);

/**
 * @brief Utility function to convert a byte array hash to a hex string.
 */
void crypto_hash_to_str(const uint8_t *hash, char *out_str);

/**
 * @brief Reads the signed golden reference hash provisioned into NVS by the
 *        Signer/CI system (see proposal ERD - ReferenceHash entity).
 * @return true if a reference hash was found and copied into out_hash.
 */
bool crypto_load_reference_hash(uint8_t *out_hash);

/**
 * @brief Provisions/overwrites the golden reference hash in NVS. Intended to
 *        be called from a trusted provisioning flow (factory flashing or a
 *        signed OTA acceptance step), NOT from normal runtime code paths.
 */
esp_err_t crypto_store_reference_hash(const uint8_t *hash);

#endif // CRYPTO_H
