#ifndef ROLLBACK_H
#define ROLLBACK_H

#include <stdbool.h>

/**
 * @brief Initializes the anti-rollback subsystem, loading the persisted
 *        minimum-allowed-version counter from NVS (or seeding it with
 *        ROLLBACK_BASELINE_VERSION on first-ever boot).
 */
void rollback_init(void);

/**
 * @brief Checks whether running_version is allowed to boot, i.e. is not
 *        older than the persisted minimum-allowed-version counter.
 */
bool rollback_check_version(int running_version);

/**
 * @brief Advances the persisted minimum-allowed-version counter to
 *        running_version if it is newer than what's currently stored.
 *        Call this only AFTER integrity has been verified for the running
 *        image, so a verified-good version becomes the new rollback floor.
 *        The counter is monotonic: it can only move forward.
 */
void rollback_commit_version(int running_version);

#endif // ROLLBACK_H
