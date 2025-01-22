import time
from collections import defaultdict
from typing import Dict, List

class Device:
    def __init__(self, id: int, buffer_size: int, processing_rate: int):
        self.id = id
        self.buffer_size = buffer_size  # in bytes
        self.processing_rate = processing_rate  # packets per second
        self.receive_buffer = 0  # current buffer usage in bytes
        self.credits_a = 40  # initial credits for packet type A
        self.credits_b = 20   # initial credits for packet type B
        self.transmission_rates = {}  # packets per second to other devices
        self.packets_in_buffer_a = 0
        self.packets_in_buffer_b = 0
        self.packet_ratio = {'A': 4, 'B': 1}  # ratio of packets A:B
        self.packets_processed = {'A': 0, 'B': 0}
        self.total_drops = 0  # counter for dropped packets due to overflow

class NetworkSimulation:
    def __init__(self):
        # Initialize devices with their buffer sizes (in KB)
        self.devices = {
            1: Device(1, 1024, 10),  # 1KB buffer
            2: Device(2, 1024, 10),  # 1KB buffer
            3: Device(3, 2048, 10),  # 2KB buffer
            4: Device(4, 4096, 10)   # 4KB buffer
        }
        
        # Set transmission rates
        self.setup_transmission_rates()
        
        self.packet_size = 64  # bytes
        self.simulation_time = 20  # seconds
        
    def setup_transmission_rates(self):
        rates = {
            1: {2: 10, 3: 20, 4: 30},
            2: {1: 10, 3: 20, 4: 30},
            3: {1: 10, 2: 20, 4: 30},
            4: {1: 10, 2: 20, 3: 30}
        }
        for src_id, destinations in rates.items():
            self.devices[src_id].transmission_rates = destinations

    def check_buffer_space(self, device: Device, packet_size: int) -> bool:
        return device.receive_buffer + packet_size <= device.buffer_size

    def process_packets(self, device: Device):
        # Calculate maximum packets that can be processed this second
        max_packets = min(device.processing_rate, 
                         device.packets_in_buffer_a + device.packets_in_buffer_b)
        
        if max_packets > 0:
            # Maintain 4:1 ratio for processing
            packets_a = min((max_packets * 4) // 5, device.packets_in_buffer_a)
            packets_b = min(max_packets - packets_a, device.packets_in_buffer_b)
            
            # Update buffer state
            device.packets_in_buffer_a -= packets_a
            device.packets_in_buffer_b -= packets_b
            device.receive_buffer -= (packets_a + packets_b) * self.packet_size
            
            # Update processed counts
            device.packets_processed['A'] += packets_a
            device.packets_processed['B'] += packets_b
            
            # Return credits after processing
            for _ in range(packets_a):
                device.credits_a = min(50, device.credits_a + 1)
            for _ in range(packets_b):
                device.credits_b = min(25, device.credits_b + 1)

    def attempt_transmission(self, src_device: Device, dest_device: Device, packet_type: str) -> bool:
        # Check credits
        if packet_type == 'A' and dest_device.credits_a <= 0:
            return False
        if packet_type == 'B' and dest_device.credits_b <= 0:
            return False
            
        # Check buffer space
        if not self.check_buffer_space(dest_device, self.packet_size):
            dest_device.total_drops += 1
            return False
            
        # Perform transmission
        if packet_type == 'A':
            dest_device.credits_a -= 1
            dest_device.packets_in_buffer_a += 1
        else:
            dest_device.credits_b -= 1
            dest_device.packets_in_buffer_b += 1
            
        dest_device.receive_buffer += self.packet_size
        return True

    def transmit_packets(self):
        for src_id, src_device in self.devices.items():
            for dest_id, rate in src_device.transmission_rates.items():
                dest_device = self.devices[dest_id]
                
                # Calculate packets of each type based on 4:1 ratio
                total_packets = rate
                packets_a = (total_packets * 4) // 5
                packets_b = total_packets - packets_a
                
                # Try to transmit type A packets
                for _ in range(packets_a):
                    self.attempt_transmission(src_device, dest_device, 'A')
                
                # Try to transmit type B packets
                for _ in range(packets_b):
                    self.attempt_transmission(src_device, dest_device, 'B')

    def print_status(self, current_time: int):
        print(f"\nTime: {current_time} seconds")
        print("-" * 50)
        
        total_processed = 0
        for device_id, device in self.devices.items():
            buffer_usage_percent = (device.receive_buffer / device.buffer_size) * 100
            total_processed += device.packets_processed['A'] + device.packets_processed['B']
            
            print(f"Device {device_id}:")
            print(f"  Buffer usage: {device.receive_buffer}/{device.buffer_size} bytes ({buffer_usage_percent:.2f}%)")
            print(f"  Credits A: {device.credits_a}")
            print(f"  Credits B: {device.credits_b}")
            print(f"  Packets in buffer - A: {device.packets_in_buffer_a}, B: {device.packets_in_buffer_b}")
            print(f"  Packets processed - A: {device.packets_processed['A']}, B: {device.packets_processed['B']}")
            print(f"  Dropped packets: {device.total_drops}")
        
        print(f"\nTotal packets processed across all devices: {total_processed}")
        print(f"Maximum possible packets: {800}")
        print(f"Current efficiency: {(total_processed/800)*100:.2f}%")

    def run_simulation(self):
        print("Starting network simulation...")
        for current_time in range(self.simulation_time):
            # Process packets first to free up buffer space
            for device in self.devices.values():
                self.process_packets(device)
            
            # Then transmit new packets
            self.transmit_packets()
            
            # Print status
            self.print_status(current_time)
            
            # Small delay to make output readable
            time.sleep(0.1)

# Run the simulation
if __name__ == "__main__":
    simulation = NetworkSimulation()
    simulation.run_simulation()
