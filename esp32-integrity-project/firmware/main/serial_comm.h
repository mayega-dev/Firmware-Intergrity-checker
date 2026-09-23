#ifndef SERIAL_COMM_H
#define SERIAL_COMM_H

#include <stdbool.h>
#include "driver/uart.h"
#include "sdkconfig.h"

// Single source of truth for which UART carries the dashboard alert
// protocol - value comes from Kconfig (see Kconfig.projbuild), so it's set
// per-board via `idf.py menuconfig` instead of being hardcoded per chip.
#define ALERT_UART_PORT ((uart_port_t)CONFIG_ALERT_UART_PORT_NUM)

void serial_comm_init(void);

/**
 * @brief True once serial_comm_init() has successfully installed the alert
 *        UART driver. Lets other modules (e.g. integrity_checker.c) avoid
 *        reading from a port that was never configured on this board.
 */
bool serial_comm_is_ready(void);

/**
 * @brief Sends a structured "::ALERT:level:event_code::\n" packet to the
 *        desktop dashboard app.
 * @return true if the packet was written to the UART TX buffer successfully.
 */
bool serial_comm_send_alert(const char *level, const char *event_code);

/**
 * @brief Sends a one-shot "::STATUS:fw_version:hardware_revision::\n"
 *        identity packet. Call this once after serial_comm_init() succeeds
 *        so a listening dashboard app knows what it's talking to, without
 *        having to guess from the alert stream alone (which only ever
 *        carries level:event_code, not device identity).
 * @return true if the packet was written to the UART TX buffer successfully.
 */
bool serial_comm_send_status(const char *fw_version, const char *hardware_revision);

#endif // SERIAL_COMM_H
