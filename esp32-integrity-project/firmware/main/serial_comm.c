#include "serial_comm.h"
#include "driver/uart.h"
#include <string.h>
#include <esp_log.h>

// IMPORTANT: whichever UART/USB peripheral ESP-IDF's console/ESP_LOG output
// is bound to must NOT also be used here, or the two data streams corrupt
// each other. That port varies by target and by menuconfig choice - it can
// be UART0 (classic default), or on native-USB chips (S2/S3/C3/C6) it can
// instead be USB-CDC or USB-Serial-JTAG. Rather than assume UART0 like a
// single-board build would, this checks the active console config at
// runtime and refuses to double-book the same UART number.
//
// Port number and TX/RX pins come from Kconfig (Kconfig.projbuild) so each
// board/chip combination can pick pins that actually exist and are free on
// its own pinout - see PORTING_NOTES.md for per-chip guidance.
#define UART_TX_PIN   CONFIG_ALERT_UART_TX_GPIO
#define UART_RX_PIN   CONFIG_ALERT_UART_RX_GPIO
#define UART_BAUD     CONFIG_ALERT_UART_BAUD_RATE
#define BUF_SIZE      1024

static const char *TAG = "SERIAL_COMM";
static bool driver_installed = false;

static bool alert_uart_collides_with_console(void) {
#if CONFIG_ESP_CONSOLE_UART
    return (uart_port_t)CONFIG_ESP_CONSOLE_UART_NUM == ALERT_UART_PORT;
#else
    // Console is on USB-CDC or USB-Serial-JTAG on this target/config, so any
    // real UART number (0/1/2) is free to use for the alert channel.
    return false;
#endif
}

void serial_comm_init(void) {
    if (alert_uart_collides_with_console()) {
        ESP_LOGE(TAG, "ALERT_UART_PORT_NUM matches the console UART - fix this in "
                      "`idf.py menuconfig` (Firmware Integrity Checker) before flashing.");
        return;
    }

    const uart_config_t uart_config = {.baud_rate = UART_BAUD,
                                       .data_bits = UART_DATA_8_BITS,
                                       .parity = UART_PARITY_DISABLE,
                                       .stop_bits = UART_STOP_BITS_1,
                                       .flow_ctrl = UART_HW_FLOWCTRL_DISABLE};

    esp_err_t err = uart_driver_install(ALERT_UART_PORT, BUF_SIZE * 2, 0, 0, NULL, 0);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to install UART driver on port %d (0x%x)", ALERT_UART_PORT, err);
        return;
    }

    err = uart_param_config(ALERT_UART_PORT, &uart_config);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to configure UART port %d (0x%x)", ALERT_UART_PORT, err);
        return;
    }

    err = uart_set_pin(ALERT_UART_PORT, UART_TX_PIN, UART_RX_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to assign UART pins (0x%x)", err);
        return;
    }

    driver_installed = true;
}

bool serial_comm_is_ready(void) {
    return driver_installed;
}

static bool write_packet(const char *packet, int len) {
    if (len < 0 || len >= 128) {
        return false;
    }
    int written = uart_write_bytes(ALERT_UART_PORT, packet, len);
    return written == len;
}

bool serial_comm_send_alert(const char *level, const char *event_code) {
    if (!driver_installed) {
        ESP_LOGE(TAG, "Cannot send alert - UART driver not initialized");
        return false;
    }

    char packet[128];
    // Structured format the dashboard app's parser reads explicitly. (Any
    // language/OS toolkit works on the host side - PySide6, Electron, a
    // plain pyserial script, etc. - as long as it opens the matching
    // COM port/tty and speaks this framing.)
    int len = snprintf(packet, sizeof(packet), "::ALERT:%s:%s::\n", level, event_code);
    if (!write_packet(packet, len)) {
        ESP_LOGE(TAG, "Alert packet truncated or encoding failed for event '%s'", event_code);
        return false;
    }
    return true;
}

bool serial_comm_send_status(const char *fw_version, const char *hardware_revision) {
    if (!driver_installed) {
        ESP_LOGE(TAG, "Cannot send status - UART driver not initialized");
        return false;
    }

    char packet[128];
    int len = snprintf(packet, sizeof(packet), "::STATUS:%s:%s::\n", fw_version, hardware_revision);
    if (!write_packet(packet, len)) {
        ESP_LOGE(TAG, "Status packet truncated or encoding failed");
        return false;
    }
    return true;
}
