from typing import Optional, List, Union, Tuple, Callable, Dict, Any

class MotorCommandBuilder:
    """Builder class for creating Modbus commands for the motor controller."""
    
    @staticmethod
    def read_actual_position() -> bytes:
        """
        Creates a command to read the actual position (0x6064).
        
        Returns:
            bytes: Command bytes for reading the actual position
        """
        return bytes([0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 0x60, 0x64, 0x00, 0, 0, 0, 4, 0, 0])

    @staticmethod
    def profile_position_command(target_pos: int) -> bytes:
        """
        Creates a command to set the target position.
        
        Args:
            target_pos: Target position in motor units
            
        Returns:
            bytes: Command bytes for setting the target position
        """
        cmd = bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 122, 0, 0, 0, 0, 4])
        cmd.extend(target_pos.to_bytes(4, byteorder='little', signed=True))
        return bytes(cmd)

    @staticmethod
    def profile_accel_command(accel: int) -> bytes:
        """
        Creates a command to set the acceleration.
        
        Args:
            accel: Acceleration value in motor units
            
        Returns:
            bytes: Command bytes for setting the acceleration
        """
        cmd = bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 131, 0, 0, 0, 0, 4])
        cmd.extend(accel.to_bytes(4, byteorder='little', signed=True))
        return bytes(cmd)

    @staticmethod
    def profile_velocity_command(velocity: int) -> bytes:
        """
        Creates a command to set the velocity.
        
        Args:
            velocity: Velocity value in motor units
            
        Returns:
            bytes: Command bytes for setting the velocity
        """
        cmd = bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 129, 0, 0, 0, 0, 4])
        cmd.extend(velocity.to_bytes(4, byteorder='little', signed=True))
        return bytes(cmd)

    @staticmethod
    def start_profile_position() -> bytes:
        """
        Creates a command to start profile position mode.
        
        Returns:
            bytes: Command bytes for starting profile position mode
        """
        return bytes([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0])

    @staticmethod
    def set_homing_method(method: int) -> bytes:
        """
        Creates a command to set the homing method.
        
        Args:
            method: Homing method ID (1-35)
            
        Returns:
            bytes: Command bytes for setting the homing method
        """
        cmd = bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 152, 0, 0, 0, 0, 1])
        cmd.append(method)
        return bytes(cmd)

    @staticmethod
    def homing_speed_config(search_vel: int, zero_vel: int, accel: int) -> List[bytes]:
        """
        Creates commands to configure homing speeds.
        
        Args:
            search_vel: Search velocity in motor units
            zero_vel: Zero velocity in motor units
            accel: Acceleration in motor units
            
        Returns:
            List[bytes]: List of command bytes for configuring homing speeds
        """
        sv = search_vel.to_bytes(4, byteorder='little', signed=True)
        zv = zero_vel.to_bytes(4, byteorder='little', signed=True)
        ac = accel.to_bytes(4, byteorder='little', signed=True)
        
        cmd1 = bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 153, 1, 0, 0, 0, 4])
        cmd1.extend(sv)
        
        cmd2 = bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 153, 2, 0, 0, 0, 4])
        cmd2.extend(zv)
        
        cmd3 = bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 154, 0, 0, 0, 0, 4])
        cmd3.extend(ac)
        
        return [bytes(cmd1), bytes(cmd2), bytes(cmd3)]

    @staticmethod
    def get_mode(mode: int) -> bytes:
        """
        Creates a command to set the operation mode.
        
        Args:
            mode: Operation mode ID
            
        Returns:
            bytes: Command bytes for setting the operation mode
        """
        return bytes([0, 0, 0, 0, 0, 14, 0, 43, 13, 1, 0, 0, 96, 96, 0, 0, 0, 0, 1, mode])

    @staticmethod
    def shutdown() -> bytes:
        """
        Creates a command to shutdown the motor.
        
        Returns:
            bytes: Command bytes for shutdown
        """
        return bytes([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 6, 0])

    @staticmethod
    def switch_on() -> bytes:
        """
        Creates a command to switch on the motor.
        
        Returns:
            bytes: Command bytes for switching on
        """
        return bytes([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 7, 0])

    @staticmethod
    def enable_operation() -> bytes:
        """
        Creates a command to enable motor operation.
        
        Returns:
            bytes: Command bytes for enabling operation
        """
        return bytes([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 15, 0])

    @staticmethod
    def read_statusword() -> bytes:
        """
        Creates a command to read the status word.
        
        Returns:
            bytes: Command bytes for reading the status word
        """
        return bytes([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2])

    @staticmethod
    def fault_reset() -> bytes:
        """
        Creates a command to reset faults.
        
        Returns:
            bytes: Command bytes for resetting faults
        """
        return bytes([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 128, 0])

    @staticmethod
    def reset_driver() -> bytes:
        """
        Creates a command to reset the driver.
        
        Returns:
            bytes: Command bytes for resetting the driver
        """
        return bytes([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 0, 1])

    @staticmethod
    def start_homing() -> bytes:
        """
        Creates a command to start the homing procedure.
        
        Returns:
            bytes: Command bytes for starting homing
        """
        return bytes([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0])

    @staticmethod
    def get_homing_status() -> bytes:
        """
        Creates a command to read the homing status.
        
        Returns:
            bytes: Command bytes for reading homing status
        """
        return bytes([0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 32, 20, 0, 0, 0, 0, 2, 0, 0])

    @staticmethod
    def get_status() -> bytes:
        """
        Creates a command to read the general status.
        
        Returns:
            bytes: Command bytes for reading general status
        """
        return bytes([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2])
    @staticmethod
    def shutdown() -> bytes:
        return bytes([0, 0, 0, 0, 0, 15, 0, 43,13, 1, 0, 0, 96, 64, 0, 0,0, 0, 2, 6, 0])
    @staticmethod
    def switch_on() -> bytes:
        return bytes([0, 0, 0, 0, 0, 15, 0, 43,13, 1, 0, 0, 96, 64, 0, 0,0, 0, 2, 7, 0])
    @staticmethod
    def enable_operation() -> bytes:
        return bytes([0, 0, 0, 0, 0, 15, 0, 43,13, 1, 0, 0, 96, 64, 0, 0,0, 0, 2, 15, 0])
    @staticmethod
    def read_statusword() -> bytes:
        return bytes([0, 0, 0, 0, 0, 13, 0, 43,13, 0, 0, 0, 96, 65, 0, 0,0, 0, 2])
    @staticmethod
    def fault_reset() -> bytes:
        return bytes([0, 0, 0, 0, 0, 15, 0, 43,13, 1, 0, 0, 96, 64, 0, 0,0, 0, 2, 128, 0])
    @staticmethod
    def reset_driver() -> bytes:
        return bytes([0, 0, 0, 0, 0, 15, 0, 43,13, 1, 0, 0, 96, 64, 0, 0,0, 0, 2, 0, 1])
    @staticmethod
    def feed_const_1() -> bytes:
        return bytes([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 1, 0, 0, 0, 4, 24, 21, 0, 0])
    @staticmethod
    def feed_const_2() -> bytes:
        return bytes([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 2, 0, 0, 0, 4, 1, 0, 0, 0])
    @staticmethod
    def homing_speed_switch() -> bytes:
        return bytes([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 153, 1, 0, 0, 0, 4, 232, 3, 0, 0])
    @staticmethod
    def homing_speed_zero() -> bytes:
        return bytes([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 153, 2, 0, 0, 0, 4, 232, 3, 0, 0])
    @staticmethod
    def homing_acc() -> bytes:
        return bytes([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 154, 0, 0, 0, 0, 2, 232, 3, 0, 0])
    @staticmethod
    def start_homing() -> bytes:
        return bytes([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0])
    @staticmethod
    def get_homing_status() -> bytes:
        return bytes([0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 32, 20, 0, 0, 0, 0, 2, 0, 0])
    @staticmethod
    def get_status() -> bytes:
        return bytes([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2])
