"""
RONGTA Thermal Printer - Python Interface
Uses python-escpos library to communicate with ESC/POS compatible printers

Installation:
    pip install python-escpos pyusb pillow
    brew install libusb  # macOS only

If USB detection fails, you may need to:
    export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
"""

import os
import sys

# Set library path for libusb on macOS (Homebrew)
if sys.platform == "darwin":
    homebrew_lib = "/opt/homebrew/lib"
    if os.path.exists(homebrew_lib):
        os.environ["DYLD_LIBRARY_PATH"] = homebrew_lib + ":" + os.environ.get("DYLD_LIBRARY_PATH", "")

from escpos.printer import Usb, Serial
import usb.core
import usb.util


def find_printer():
    """
    Find connected USB printers and display their info.
    Returns a list of tuples (vendor_id, product_id, description)
    """
    printers = []
    
    print("🔍 Scanning for USB devices...\n")
    
    try:
        devices = usb.core.find(find_all=True)
    except usb.core.NoBackendError:
        print("❌ No USB backend available.")
        print("   On macOS, try: brew install libusb")
        print("   Then restart your terminal or run:")
        print("   export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH\n")
        return printers
    
    for device in devices:
        try:
            vendor_id = device.idVendor
            product_id = device.idProduct
            
            try:
                manufacturer = usb.util.get_string(device, device.iManufacturer) or "Unknown"
            except:
                manufacturer = "Unknown"
            
            try:
                product = usb.util.get_string(device, device.iProduct) or "Unknown"
            except:
                product = "Unknown"
            
            # Common thermal printer vendor IDs
            thermal_vendors = {
                0x0416: "RONGTA",
                0x0483: "STMicroelectronics (common for thermal printers)",
                0x04B8: "Epson",
                0x0525: "Generic Thermal Printer",
                0x1504: "RONGTA",
                0x0FE6: "Generic Printer",
                0x1FC9: "NXP (common for thermal printers)",
                0x28E9: "RONGTA",
                0x1A86: "QinHeng (common for thermal printers)",
            }
            
            is_printer = vendor_id in thermal_vendors or "printer" in product.lower()
            
            if is_printer or "rongta" in manufacturer.lower() or "rongta" in product.lower():
                print(f"✅ FOUND PRINTER:")
                print(f"   Vendor ID:  0x{vendor_id:04x}")
                print(f"   Product ID: 0x{product_id:04x}")
                print(f"   Manufacturer: {manufacturer}")
                print(f"   Product: {product}")
                print()
                printers.append((vendor_id, product_id, f"{manufacturer} - {product}"))
            
        except Exception as e:
            pass
    
    if not printers:
        print("⚠️  No thermal printers auto-detected. Listing all USB devices:\n")
        for device in usb.core.find(find_all=True):
            try:
                product = usb.util.get_string(device, device.iProduct) or ""
            except:
                product = ""
            print(f"   Vendor: 0x{device.idVendor:04x}, Product: 0x{device.idProduct:04x} - {product}")
    
    return printers


def print_message(message, vendor_id=0x0416, product_id=0x5011):
    """
    Print a simple message to the RONGTA thermal printer.
    
    Args:
        message: The text message to print
        vendor_id: USB Vendor ID (default 0x0416 for RONGTA)
        product_id: USB Product ID (default 0x5011, common for RONGTA)
    """
    try:
        # Connect to the printer via USB
        printer = Usb(vendor_id, product_id)
        
        # Initialize printer
        printer.set(align='center')
        
        # Print the message
        printer.text("\n")
        printer.text("=" * 32 + "\n")
        printer.text("\n")
        
        # Set text properties
        printer.set(align='center', font='a', bold=True, double_height=True, double_width=True)
        printer.text("PHOTOBOOTH\n")
        
        printer.set(align='center', font='a', bold=False, double_height=False, double_width=False)
        printer.text("\n")
        printer.text(message + "\n")
        printer.text("\n")
        printer.text("=" * 32 + "\n")
        printer.text("\n\n\n")
        
        # Cut the paper (if printer supports it)
        try:
            printer.cut()
        except:
            pass
        
        printer.close()
        print(f"✅ Message printed successfully!")
        return True
        
    except usb.core.USBError as e:
        if "Access denied" in str(e) or "Resource busy" in str(e):
            print(f"❌ USB Access Error: {e}")
            print("   Try unplugging and replugging the printer,")
            print("   or run the script with sudo.")
        else:
            print(f"❌ USB Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error printing: {e}")
        return False


def print_receipt(title, lines, footer=None, vendor_id=0x0416, product_id=0x5011):
    """
    Print a formatted receipt with title, content lines, and optional footer.
    
    Args:
        title: Title text (printed large and centered)
        lines: List of strings to print
        footer: Optional footer text
        vendor_id: USB Vendor ID
        product_id: USB Product ID
    """
    try:
        printer = Usb(vendor_id, product_id)
        
        # Header
        printer.set(align='center', bold=True, double_height=True, double_width=True)
        printer.text(f"\n{title}\n")
        printer.set(align='center', bold=False, double_height=False, double_width=False)
        printer.text("=" * 32 + "\n\n")
        
        # Content
        printer.set(align='left')
        for line in lines:
            printer.text(f"{line}\n")
        
        # Footer
        if footer:
            printer.text("\n" + "-" * 32 + "\n")
            printer.set(align='center')
            printer.text(f"{footer}\n")
        
        printer.text("\n\n\n")
        
        try:
            printer.cut()
        except:
            pass
        
        printer.close()
        print(f"✅ Receipt printed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error printing receipt: {e}")
        return False


def print_image(image_path, vendor_id=0x0416, product_id=0x5011):
    """
    Print an image to the thermal printer.
    
    Args:
        image_path: Path to the image file
        vendor_id: USB Vendor ID
        product_id: USB Product ID
    """
    try:
        from PIL import Image
        
        printer = Usb(vendor_id, product_id)
        
        # Print the image
        printer.image(image_path)
        printer.text("\n\n\n")
        
        try:
            printer.cut()
        except:
            pass
        
        printer.close()
        print(f"✅ Image printed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error printing image: {e}")
        return False


# Default RONGTA vendor/product IDs to try
RONGTA_IDS = [
    (0x0416, 0x5011),  # Common RONGTA
    (0x1504, 0x0006),  # RONGTA RPP-series
    (0x28E9, 0x0289),  # RONGTA
    (0x0483, 0x5720),  # STM-based RONGTA
    (0x1A86, 0x7523),  # CH340 USB-Serial (common for cheap thermal printers)
]


if __name__ == "__main__":
    print("🖨️  RONGTA Thermal Printer Test\n")
    print("-" * 40)
    
    # First, find connected printers
    printers = find_printer()
    
    if printers:
        vendor_id, product_id, desc = printers[0]
        print(f"\n📝 Using printer: {desc}")
        print(f"   IDs: 0x{vendor_id:04x}, 0x{product_id:04x}\n")
        
        # Print a test message
        print_message(
            "Hello from Python!\nThis is a test print.",
            vendor_id=vendor_id,
            product_id=product_id
        )
    else:
        print("\n💡 Tips:")
        print("   1. Make sure your printer is connected and powered on")
        print("   2. Check System Information > USB for your printer's IDs")
        print("   3. You may need to run: sudo python3 thermal_printer.py")
        print()
        
        # Try default RONGTA IDs
        print("🔄 Attempting with common RONGTA IDs...")
        for vid, pid in RONGTA_IDS:
            print(f"   Trying 0x{vid:04x}, 0x{pid:04x}...", end=" ")
            if print_message("Hello from Python!\nThis is a test print.", vid, pid):
                break
            print()
