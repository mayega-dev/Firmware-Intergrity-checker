#ifndef LOGGER_H
#define LOGGER_H

#include <stdint.h>
#include <stdbool.h>

/**
 * @brief Logs local events to NVS (Non-Volatile Storage) as a wear-aware
 *        ring buffer, bounded by SECURE_LOG_MAX_ENTRIES.
 */
void logger_init(void);

/**
 * @brief Records a security event. Persists to NVS (in addition to the
 *        live ESP_LOG console output) so the entry survives reboot and can
 *        be retrieved for forensic export, per the proposal's IntegrityLog
 *        design.
 */
void logger_log_event(const char *event_type, const char *message);

/**
 * @brief Returns the number of log entries currently stored.
 */
uint32_t logger_get_entry_count(void);

/**
 * @brief Fetches a stored log entry by its logical index (0 = oldest entry
 *        still retained). Returns true and fills out_type/out_message on
 *        success. out_type and out_message buffers must be at least
 *        LOG_ENTRY_MSG_MAX_LEN bytes.
 */
bool logger_get_entry(uint32_t index, char *out_type, char *out_message);

#endif // LOGGER_H
