#ifndef FIRMWARE_CONFIG_H
#define FIRMWARE_CONFIG_H

#define FIRMWARE_VERSION_MAJOR    1
#define FIRMWARE_VERSION_MINOR    0
#define FIRMWARE_VERSION_PATCH    0

/**
 * @brief Hardware Revision String (multi-target)
 * No longer pinned to the ESP32-S3. CONFIG_IDF_TARGET_* is defined
 * automatically by ESP-IDF based on `idf.py set-target <chip>`, so the same
 * source tree labels itself correctly for whichever chip it was built for,
 * instead of a hardcoded string that would be silently wrong on a plain
 * ESP32, an ESP32-C3, an ESP32-C6, etc.
 * Optionally override BOARD_MODULE_SUFFIX at build time, e.g.
 *   idf.py build -DBOARD_MODULE_SUFFIX='"-N8R8"'
 * to keep tracking flash/PSRAM module variants per physical board.
 */
#ifndef BOARD_MODULE_SUFFIX
#define BOARD_MODULE_SUFFIX ""
#endif

#if defined(CONFIG_IDF_TARGET_ESP32)
#define HARDWARE_REVISION "ESP32" BOARD_MODULE_SUFFIX
#elif defined(CONFIG_IDF_TARGET_ESP32S2)
#define HARDWARE_REVISION "ESP32-S2" BOARD_MODULE_SUFFIX
#elif defined(CONFIG_IDF_TARGET_ESP32S3)
#define HARDWARE_REVISION "ESP32-S3" BOARD_MODULE_SUFFIX
#elif defined(CONFIG_IDF_TARGET_ESP32C2)
#define HARDWARE_REVISION "ESP32-C2" BOARD_MODULE_SUFFIX
#elif defined(CONFIG_IDF_TARGET_ESP32C3)
#define HARDWARE_REVISION "ESP32-C3" BOARD_MODULE_SUFFIX
#elif defined(CONFIG_IDF_TARGET_ESP32C6)
#define HARDWARE_REVISION "ESP32-C6" BOARD_MODULE_SUFFIX
#elif defined(CONFIG_IDF_TARGET_ESP32H2)
#define HARDWARE_REVISION "ESP32-H2" BOARD_MODULE_SUFFIX
#else
#define HARDWARE_REVISION "ESP32-UNKNOWN-TARGET" BOARD_MODULE_SUFFIX
#endif

/**
 * @brief Per-target capability notes (see PORTING_NOTES.md):
 *  - SHA-256 hardware acceleration exists on ESP32, S2, S3, C3, C6, H2 in
 *    IDF's mbedTLS integration; it's toggled by the Kconfig option
 *    CONFIG_MBEDTLS_HARDWARE_SHA (menuconfig), not by a code change here -
 *    crypto.c calls the portable mbedtls_sha256_* API either way.
 *  - Console/log UART: on chips with native USB (S2/S3/C3/C6 devkits) the
 *    console can be routed to USB-CDC or USB-Serial-JTAG instead of UART0.
 *    serial_comm.c now reads the alert-UART pin/port assignment from
 *    Kconfig instead of a hardcoded UART_NUM_1/GPIO17/18, so it can be
 *    matched to whatever pins are actually free on the target board.
 */

#define MONITORED_PARTITION_LABEL "factory"
#define RUNTIME_CHECK_INTERVAL_MS 10000
#define SECURE_LOG_MAX_ENTRIES    100

#define USE_HARDWARE_SHA256_ACCEL 1
#define ENFORCE_ANTI_ROLLBACK     1

#define SECURITY_PANIC_REACTION   1

#define ROLLBACK_NVS_NAMESPACE     "rb_prot"
#define ROLLBACK_NVS_KEY_MIN_VER   "min_ver"
#define ROLLBACK_BASELINE_VERSION  1

#define REFHASH_NVS_NAMESPACE      "ref_hash"
#define REFHASH_NVS_KEY            "golden"

#define LOG_NVS_NAMESPACE          "sec_log"
#define LOG_NVS_KEY_COUNT          "count"
#define LOG_NVS_KEY_HEAD           "head"
#define LOG_ENTRY_MSG_MAX_LEN      64

#ifndef ENABLE_TAMPER_SIMULATION
#define ENABLE_TAMPER_SIMULATION 0
#endif

#endif // FIRMWARE_CONFIG_H
