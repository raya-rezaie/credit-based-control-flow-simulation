import time
from collections import deque
import random

class CumulativeStats:
    def __init__(self):
        self.total_packets_sent = 0
        self.total_packets_received = 0
        self.total_packets_processed = 0
        self.total_packets_dropped = 0
        self.total_type_A_processed = 0
        self.total_type_B_processed = 0
        self.buffer_utilization_samples = []
        self.start_time = time.time()

    def update_buffer_utilization(self, current_usage, capacity):
        utilization = (current_usage / capacity) * 100
        self.buffer_utilization_samples.append(utilization)

    def get_average_buffer_utilization(self):
        if not self.buffer_utilization_samples:
            return 0
        return sum(self.buffer_utilization_samples) / len(self.buffer_utilization_samples)

    def get_runtime(self):
        return time.time() - self.start_time

class Packet:
    def __init__(self, packet_type, source, destination, size=64):
        self.type = packet_type
        self.source = source
        self.destination = destination
        self.size = size
        self.timestamp = time.time()

class Device:
    def __init__(self, id, receive_buffer_size):
        self.id = id
        self.receive_buffer_size = receive_buffer_size
        self.receive_buffer = deque()
        self.send_rates = {}
        self.credits = {}
        self.processing_rate = 10  # packets per second
        self.processed_packets = 0
        self.received_packets = 0
        self.dropped_packets = 0
        self.packets_type_A = 0
        self.packets_type_B = 0
        self.last_process_time = time.time()
        self.sent_packets = 0
        self.stats = CumulativeStats()
        self.last_processed_count = 0
        
    def get_available_buffer_space(self):
        used_space = sum(packet.size for packet in self.receive_buffer)
        return self.receive_buffer_size - used_space
    
    def can_receive_packet(self, packet_size):
        return self.get_available_buffer_space() >= packet_size
    
    def receive_packet(self, packet):
        if self.can_receive_packet(packet.size):
            self.receive_buffer.append(packet)
            self.received_packets += 1
            self.stats.total_packets_received += 1
            if packet.type == 'A':
                self.packets_type_A += 1
            else:
                self.packets_type_B += 1
            return True
        self.dropped_packets += 1
        self.stats.total_packets_dropped += 1
        return False
    
    def process_packets(self, current_second):
        # Calculate how many packets should have been processed by this time
        total_should_process = int(current_second * self.processing_rate)
        packets_to_process = total_should_process - self.last_processed_count
        
        processed_packets_this_cycle = 0
        for _ in range(min(packets_to_process, len(self.receive_buffer))):
            if self.receive_buffer:
                packet = self.receive_buffer.popleft()
                self.processed_packets += 1
                processed_packets_this_cycle += 1
                if packet.type == 'A':
                    self.stats.total_type_A_processed += 1
                else:
                    self.stats.total_type_B_processed += 1
        
        self.stats.total_packets_processed += processed_packets_this_cycle
        self.last_processed_count = total_should_process
        
        # Update buffer utilization statistics
        current_usage = self.receive_buffer_size - self.get_available_buffer_space()
        self.stats.update_buffer_utilization(current_usage, self.receive_buffer_size)
    
    def get_state_info(self):
        return {
            'buffer_usage': self.receive_buffer_size - self.get_available_buffer_space(),
            'buffer_capacity': self.receive_buffer_size,
            'packets_in_buffer': len(self.receive_buffer),
            'processed_packets': self.processed_packets,
            'received_packets': self.received_packets,
            'dropped_packets': self.dropped_packets,
            'packets_type_A': self.packets_type_A,
            'packets_type_B': self.packets_type_B,
            'sent_packets': self.sent_packets
        }

class Switch:
    def __init__(self, devices):
        self.devices = devices
        self.initialize_credits()
        
    def initialize_credits(self):
        for device in self.devices:
            device.credits = {
                other_device.id: other_device.receive_buffer_size 
                for other_device in self.devices 
                if other_device.id != device.id
            }
    
    def update_credits(self, source_id, dest_id, packet_size):
        source_device = next(d for d in self.devices if d.id == source_id)
        source_device.credits[dest_id] -= packet_size
        
    def return_credits(self, source_id, dest_id, packet_size):
        source_device = next(d for d in self.devices if d.id == source_id)
        source_device.credits[dest_id] += packet_size

def print_device_states(devices, current_second):
    print(f"\n=== Time: {current_second} seconds ===")
    for device in devices:
        state = device.get_state_info()
        print(f"\nDevice {device.id}:")
        print(f"Buffer Usage: {state['buffer_usage']}/{state['buffer_capacity']} bytes")
        print(f"Packets in Buffer: {state['packets_in_buffer']}")
        print(f"Processed Packets: {state['processed_packets']}")
        print(f"Received Packets: {state['received_packets']}")
        print(f"Dropped Packets: {state['dropped_packets']}")
        print(f"Type A Packets: {state['packets_type_A']}")
        print(f"Type B Packets: {state['packets_type_B']}")
        print(f"Sent Packets: {state['sent_packets']}")

def print_cumulative_stats(devices):
    print("\n=== Cumulative Statistics ===")
    all_devices_stats = {
        'total_sent': sum(device.stats.total_packets_sent for device in devices),
        'total_received': sum(device.stats.total_packets_received for device in devices),
        'total_processed': sum(device.stats.total_packets_processed for device in devices),
        'total_dropped': sum(device.stats.total_packets_dropped for device in devices),
        'total_type_A': sum(device.stats.total_type_A_processed for device in devices),
        'total_type_B': sum(device.stats.total_type_B_processed for device in devices)
    }
    
    print("\nNetwork-wide Statistics:")
    print(f"Total Packets Sent: {all_devices_stats['total_sent']}")
    print(f"Total Packets Received: {all_devices_stats['total_received']}")
    print(f"Total Packets Processed: {all_devices_stats['total_processed']}")
    print(f"Total Packets Dropped: {all_devices_stats['total_dropped']}")
    print(f"Total Type A Packets Processed: {all_devices_stats['total_type_A']}")
    print(f"Total Type B Packets Processed: {all_devices_stats['total_type_B']}")
    
    print("\nPer-Device Average Buffer Utilization:")
    for device in devices:
        avg_util = device.stats.get_average_buffer_utilization()
        print(f"Device {device.id}: {avg_util:.2f}%")

def simulate(duration_seconds):
    print("Starting Network Simulation...")
    print("Initializing devices...")
    
    # Initialize devices with their buffer sizes
    devices = [
        Device(1, 1024),  # 1 KB
        Device(2, 1024),  # 1 KB
        Device(3, 2048),  # 2 KB
        Device(4, 4096)   # 4 KB
    ]
    
    # Set transmission rates (packets per second)
    transmission_rates = {
        1: {2: 10, 3: 20, 4: 30},
        2: {1: 10, 3: 20, 4: 30},
        3: {1: 10, 2: 20, 4: 30},
        4: {1: 10, 2: 20, 3: 30}
    }
    
    for device in devices:
        device.send_rates = transmission_rates[device.id]
    
    switch = Switch(devices)
    
    # Simulation loop
    start_time = time.time()
    last_print_time = start_time
    current_time = start_time
    
    while current_time - start_time < duration_seconds:
        current_second = int(current_time - start_time)
        
        # Generate and transmit packets
        for source_device in devices:
            for dest_id, rate in source_device.send_rates.items():
                packets_to_send = int((current_time - start_time) * rate) - \
                                int((current_time - start_time - 0.1) * rate)
                
                dest_device = next(d for d in devices if d.id == dest_id)
                
                # Try to send packets if we have credits
                for _ in range(packets_to_send):
                    if source_device.credits[dest_id] >= 64:
                        packet_type = 'A' if random.random() < 0.5 else 'B'
                        packet = Packet(packet_type, source_device.id, dest_id)
                        
                        if dest_device.can_receive_packet(packet.size):
                            dest_device.receive_packet(packet)
                            switch.update_credits(source_device.id, dest_id, packet.size)
                            source_device.sent_packets += 1
                            source_device.stats.total_packets_sent += 1
        
        # Process packets in each device
        for device in devices:
            device.process_packets(current_second)
            
            # Return credits for processed packets
            for processed_packet in device.receive_buffer:
                switch.return_credits(
                    processed_packet.source,
                    device.id,
                    processed_packet.size
                )
        
        # Print states every second
        if int(current_time - last_print_time) >= 1:
            print_device_states(devices, current_second)
            last_print_time = current_time
        
        # Small sleep to prevent CPU overload
        time.sleep(0.01)
        current_time = time.time()
    
    # Print final statistics
    print("\n=== Final Device States ===")
    print_device_states(devices, duration_seconds)
    print_cumulative_stats(devices)
    print("\nSimulation completed!")

if __name__ == "__main__":
    simulate(20)  # Run simulation for 20 seconds
