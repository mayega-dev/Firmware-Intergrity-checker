#include "integrity_checker.h"
#include "crypto.h"
#include "logger.h"
#include "rollback.h"
#include "serial_comm.h"
#include "firmware_config.h"
#include "driver/uart.h"
#include <esp_log.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <string.h>

static const char *TAG = "INTEGRITY_MONITOR";
static uint8_t golden_baseline_hash[HASH_SIZE_BYTES];
static bool is_baseline_set = false;
static bool baseline_is_trusted_reference = false; // true = provisioned by Signer/CI, not self-established

#if ENABLE_TAMPER_SIMULATION
static bool simulate_tamper_attack = false; // DEBUG-ONLY: simulates a hack for testing. Never enable in release builds.
#endif

// Shares the dedicated alert/control UART configured in serial_comm.c.
// ALERT_UART_PORT is defined once, in serial_comm.h (from Kconfig), and
// reused here instead of a second hardcoded constant that could silently
// drift out of sync when porting to a different board/chip.
#define RX_BUF_SIZE 1024

static void handle_verification_failure(void) {
    logger_log_event("INTEGRITY_FAIL", "Memory mismatch in app partition");
    serial_comm_send_alert("CRITICAL", "FIRMWARE_TAMPERED");

#if SECURITY_PANIC_REACTION == 2
    ESP_LOGE(TAG, "Security panic reaction: triggering software reset.");
    vTaskDelay(pdMS_TO_TICKS(200)); // give the alert time to flush over UART
    esp_restart();
#else
    ESP_LOGE(TAG, "Security panic reaction: halting further automated verification.");
#endif
}

static void integrity_checker_task(void *pvParameters) {
    ESP_LOGI(TAG, "Runtime Integrity Monitor Started.");

    // Prefer a signed golden reference provisioned by the Signer/CI system
    // (proposal ERD: ReferenceHash entity) over a self-established baseline.
    // A self-established baseline only proves the image hasn't changed SINCE
    // boot - it can't detect firmware that was already tampered with before
    // this boot, since it trusts whatever was in flash at startup.
    if (crypto_load_reference_hash(golden_baseline_hash)) {
        is_baseline_set = true;
        baseline_is_trusted_reference = true;
        ESP_LOGI(TAG, "Golden reference hash loaded from provisioned NVS store.");
    } else if (crypto_calculate_partition_hash(MONITORED_PARTITION_LABEL, golden_baseline_hash) == ESP_OK) {
        is_baseline_set = true;
        baseline_is_trusted_reference = false;
        ESP_LOGW(TAG, "No provisioned reference hash found - falling back to a self-established "
                      "runtime baseline. This does NOT protect against firmware tampered before boot; "
                      "provision a signed reference via crypto_store_reference_hash() during manufacturing.");
    }

    if (is_baseline_set && baseline_is_trusted_reference) {
        // The image matches its signed reference at boot - safe to advance the
        // anti-rollback floor to the currently running version.
        rollback_commit_version(FIRMWARE_VERSION_MAJOR);
    }

    uint8_t rx_data[RX_BUF_SIZE];
    int64_t elapsed_ms = 0;

    while (1) {
        // 1. Check for incoming control commands from the Desktop App
        int len;
        if (serial_comm_is_ready()) {
            len = uart_read_bytes(ALERT_UART_PORT, rx_data, RX_BUF_SIZE - 1, pdMS_TO_TICKS(100));
        } else {
            vTaskDelay(pdMS_TO_TICKS(100)); // keep the same ~100ms cadence without a live UART
            len = 0;
        }
        elapsed_ms += 100;

        if (len > 0) {
            rx_data[len] = '\0';
            char *msg = (char *)rx_data;

            if (strstr(msg, "::POLL::") != NULL) {
                ESP_LOGI(TAG, "Manual poll requested by dashboard engine.");
                integrity_checker_verify_now();
            }
#if ENABLE_TAMPER_SIMULATION
            else if (strstr(msg, "::TAMPER::") != NULL) {
                ESP_LOGW(TAG, "DEBUG BUILD: Injecting a simulated runtime tamper attack command!");
                simulate_tamper_attack = true;
                integrity_checker_verify_now();
            }
#endif
        }

        // 2. Automated Periodic Verification Sweep
        if (elapsed_ms >= RUNTIME_CHECK_INTERVAL_MS) {
            elapsed_ms = 0;
            if (is_baseline_set
#if ENABLE_TAMPER_SIMULATION
                && !simulate_tamper_attack
#endif
            ) {
                integrity_checker_verify_now();
            }
        }
    }
}

bool integrity_checker_verify_now(void) {
    if (!is_baseline_set) {
        return false;
    }

    uint8_t current_hash[HASH_SIZE_BYTES];

    // Process verification check
    if (crypto_calculate_partition_hash(MONITORED_PARTITION_LABEL, current_hash) == ESP_OK) {
#if ENABLE_TAMPER_SIMULATION
        // DEBUG BUILD ONLY: deliberately corrupt the comparison to exercise the alert path.
        if (simulate_tamper_attack) {
            current_hash[0] ^= 0xFF;
        }
#endif

        if (memcmp(golden_baseline_hash, current_hash, HASH_SIZE_BYTES) != 0) {
            ESP_LOGE(TAG, "CRITICAL: Firmware Integrity Violation Detected!");
            handle_verification_failure();
            return false;
        } else {
            ESP_LOGI(TAG, "Runtime integrity verified: OK.");
            serial_comm_send_alert("INFO", "STATUS_SAFE");
            return true;
        }
    }
    return false;
}

void integrity_checker_init(void) {
    xTaskCreate(integrity_checker_task, "integrity_task", 4096, NULL, 5, NULL);
}
