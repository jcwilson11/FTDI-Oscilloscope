class ioRecoveryManager:
    def __init__(self):
        self.messages = []
        self.safe_stopped = False

    def notify_user(self, msg: str) -> None:
        self.messages.append(msg)
        print(f"[RecoveryManager] {msg}")

    def transition_to_safe_stop(self) -> None:
        self.safe_stopped = True
        print("[RecoveryManager] Transitioning to safe stop.")


RecoveryManager = ioRecoveryManager
