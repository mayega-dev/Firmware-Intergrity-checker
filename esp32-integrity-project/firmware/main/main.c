#include "crypto.h"
#include "integrity_checker.h"
#include "logger.h"
#include "rollback.h"
#include "serial_comm.h"
#include "firmware_config.h"
#include <esp_log.h>
#include <stdio.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

static const char *TAG = "MAIN";

void app_main(void) {
    ESP_LOGI(TAG, "Starting Firmware Security Engine v%d.%d.%d on %s...", FIRMWARE_VERSION_MAJOR,
             FIRMWARE_VERSION_MINOR, FIRMWARE_VERSION_PATCH, HARDWARE_REVISION);

    // 1. Initialize Subsystems
    logger_init();
    serial_comm_init();
    rollback_init();

    // 1b. Announce device identity to anything listening on the alert UART
    // (e.g. the PySide6 dashboard) - the alert stream otherwise only ever
    // carries level:event_code, never which device/firmware it came from.
    if (serial_comm_is_ready()) {
        char fw_version[16];
        snprintf(fw_version, sizeof(fw_version), "%d.%d.%d", FIRMWARE_VERSION_MAJOR, FIRMWARE_VERSION_MINOR,
                 FIRMWARE_VERSION_PATCH);
        serial_comm_send_status(fw_version, HARDWARE_REVISION);
    }

    // 2. Perform Pre-boot Anti-Rollback Check
    // Uses FIRMWARE_VERSION_MAJOR (single source of truth, defined in
    // firmware_config.h) instead of a separately maintained constant, so the
    // two can't drift out of sync.
    if (!rollback_check_version(FIRMWARE_VERSION_MAJOR)) {
        logger_log_event("ROLLBACK_BLOCKED", "Boot halted: firmware version below anti-rollback floor");
        serial_comm_send_alert("CRITICAL", "ROLLBACK_ATTEMPT_BLOCKED");
        ESP_LOGE(TAG, "System locked due to anti-rollback violations.");
        return; // Halt boot process
    }

    // 3. Fire up the continuous background verification task loop.
    // (integrity_checker_init() commits the new anti-rollback floor itself,
    // once it has confirmed the running image against a trusted reference.)
    integrity_checker_init();

    ESP_LOGI(TAG, "Application booted up safely. Continuous verification active.");
}
