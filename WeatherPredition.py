#!/usr/bin/env python3
"""
Weather Dashboard with GUI Popup Window
Uses tkinter for a graphical user interface
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional
import threading

class WeatherDashboardGUI:
    def __init__(self):
        self.cities = ["London", "New York", "Tokyo", "Sydney", "Paris"]
        self.weather_data = []

        # Create main window
        self.root = tk.Tk()
        self.root.title("🌤️ Weather Dashboard")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f8ff')

        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.setup_gui()

    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights for the root window and main_frame
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # ***** FIX: Add weight to the row containing the data frame *****
        # This allows the data frame to expand vertically and fill available space
        main_frame.rowconfigure(4, weight=1)

        # Title
        title_label = tk.Label(main_frame, text="🌤️ Weather Dashboard",
                               font=('Arial', 18, 'bold'),
                               bg='#f0f8ff', fg='#2c3e50')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Status label
        self.status_label = tk.Label(main_frame, text="Ready to fetch weather data",
                                     font=('Arial', 10),
                                     bg='#f0f8ff', fg='#7f8c8d')
        self.status_label.grid(row=1, column=0, columnspan=3, pady=(0, 10))

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(0, 20))

        # Fetch data button
        self.fetch_btn = tk.Button(button_frame, text="🔄 Fetch Weather Data",
                                   command=self.fetch_weather_threaded,
                                   font=('Arial', 12, 'bold'),
                                   bg='#3498db', fg='white',
                                   relief='flat', padx=20, pady=10)
        self.fetch_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Save data button
        self.save_btn = tk.Button(button_frame, text="💾 Save Data",
                                  command=self.save_data,
                                  font=('Arial', 12, 'bold'),
                                  bg='#27ae60', fg='white',
                                  relief='flat', padx=20, pady=10,
                                  state='disabled')
        self.save_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Clear button
        self.clear_btn = tk.Button(button_frame, text="🗑️ Clear",
                                   command=self.clear_data,
                                   font=('Arial', 12, 'bold'),
                                   bg='#e74c3c', fg='white',
                                   relief='flat', padx=20, pady=10)
        self.clear_btn.pack(side=tk.LEFT)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))

        # Data display frame
        data_frame = ttk.LabelFrame(main_frame, text="Weather Data", padding="10")
        data_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        data_frame.columnconfigure(0, weight=1)
        data_frame.rowconfigure(0, weight=1)

        # Treeview for data display
        columns = ('City', 'Temperature', 'Humidity', 'Pressure', 'Wind Speed', 'Description')
        self.tree = ttk.Treeview(data_frame, columns=columns, show='headings', height=10)

        # Define column headings and widths
        column_widths = {'City': 100, 'Temperature': 100, 'Humidity': 80,
                         'Pressure': 90, 'Wind Speed': 90, 'Description': 120}

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100), anchor='center')

        # Scrollbars for treeview
        v_scrollbar = ttk.Scrollbar(data_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(data_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Statistics frame
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="10")
        stats_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

        self.stats_text = tk.Text(stats_frame, height=6, width=80, font=('Courier', 10),
                                  bg='#ecf0f1', fg='#2c3e50', relief='flat')
        self.stats_text.pack(fill=tk.BOTH, expand=True)

    def fetch_weather_data(self, city: str) -> Optional[Dict]:
        """Fetch weather data for a city (mock data for demo)"""
        try:
            # Simulate API delay
            import time
            time.sleep(0.5)

            # Mock data
            mock_data = {
                "name": city,
                "main": {
                    "temp": 20 + hash(city) % 15,
                    "humidity": 50 + hash(city) % 30,
                    "pressure": 1000 + hash(city) % 50
                },
                "weather": [{"description": "clear sky"}],
                "wind": {"speed": 5 + hash(city) % 10}
            }
            return mock_data
        except Exception as e:
            print(f"Error fetching data for {city}: {e}")
            return None

    def fetch_weather_threaded(self):
        """Fetch weather data in a separate thread to prevent GUI freezing"""
        def fetch_worker():
            self.fetch_btn.config(state='disabled')
            self.progress.start()
            self.status_label.config(text="Fetching weather data...")

            self.weather_data = []

            for i, city in enumerate(self.cities):
                self.status_label.config(text=f"Fetching data for {city}...")
                weather = self.fetch_weather_data(city)

                if weather:
                    data_item = {
                        "City": weather["name"],
                        "Temperature (°C)": weather["main"]["temp"],
                        "Humidity (%)": weather["main"]["humidity"],
                        "Pressure (hPa)": weather["main"]["pressure"],
                        "Wind Speed (m/s)": weather["wind"]["speed"],
                        "Description": weather["weather"][0]["description"],
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self.weather_data.append(data_item)

            # Update GUI in main thread
            self.root.after(0, self.update_display)

        # Start worker thread
        thread = threading.Thread(target=fetch_worker, daemon=True)
        thread.start()

    def update_display(self):
        """Update the GUI display with fetched data"""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add new data
        for item in self.weather_data:
            self.tree.insert('', tk.END, values=(
                item['City'],
                f"{item['Temperature (°C)']}°C",
                f"{item['Humidity (%)']}%",
                f"{item['Pressure (hPa)']} hPa",
                f"{item['Wind Speed (m/s)']} m/s",
                item['Description']
            ))

        # Update statistics
        self.update_statistics()

        # Update UI state
        self.progress.stop()
        self.fetch_btn.config(state='normal')
        self.save_btn.config(state='normal')
        self.status_label.config(text=f"Data fetched successfully for {len(self.weather_data)} cities")

    def update_statistics(self):
        """Update the statistics display"""
        if not self.weather_data:
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, "No data available")
            return

        # Calculate statistics
        temps = [item["Temperature (°C)"] for item in self.weather_data]
        humidity = [item["Humidity (%)"] for item in self.weather_data]
        pressure = [item["Pressure (hPa)"] for item in self.weather_data]
        wind = [item["Wind Speed (m/s)"] for item in self.weather_data]

        # Find extremes
        hottest = max(self.weather_data, key=lambda x: x["Temperature (°C)"])
        coldest = min(self.weather_data, key=lambda x: x["Temperature (°C)"])

        # Create statistics text
        stats_text = f"""📊 WEATHER STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Average Temperature: {sum(temps)/len(temps):.1f}°C
Average Humidity:    {sum(humidity)/len(humidity):.1f}%
Average Pressure:    {sum(pressure)/len(pressure):.1f} hPa
Average Wind Speed:  {sum(wind)/len(wind):.1f} m/s

🔥 EXTREMES:
Hottest: {hottest['City']} ({hottest['Temperature (°C)']}°C)
Coldest: {coldest['City']} ({coldest['Temperature (°C)']}°C)

📅 Last Updated: {self.weather_data[0]['Timestamp']}"""

        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, stats_text)

    def save_data(self):
        """Save weather data to files"""
        if not self.weather_data:
            messagebox.showwarning("No Data", "No weather data to save!")
            return

        try:
            # Save as JSON
            with open("weather_data.json", "w", encoding="utf-8") as jsonfile:
                json.dump(self.weather_data, jsonfile, indent=2)

            # Save as CSV
            with open("weather_data.csv", "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = self.weather_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.weather_data)

            messagebox.showinfo("Success",
                                "Data saved successfully!\n\n"
                                "Files created:\n"
                                "• weather_data.json\n"
                                "• weather_data.csv")

            self.status_label.config(text="Data saved successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data:\n{str(e)}")

    def clear_data(self):
        """Clear all data from the display"""
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Clear statistics
        self.stats_text.delete(1.0, tk.END)

        # Clear data
        self.weather_data = []

        # Update UI state
        self.save_btn.config(state='disabled')
        self.status_label.config(text="Data cleared")

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

def main():
    """Main application entry point"""
    try:
        app = WeatherDashboardGUI()
        app.run()
    except Exception as e:
        print(f"Error starting GUI application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()