#!/usr/bin/env python3
"""
Debug Weather Dashboard - Step by step execution
"""

import json
import csv
from datetime import datetime
from typing import Dict, List, Optional

print("🐛 DEBUG: Starting application...")

class WeatherDashboard:
    def __init__(self):
        print("🐛 DEBUG: Initializing WeatherDashboard...")
        self.api_key = "demo_key"
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.cities = ["London", "New York", "Tokyo", "Sydney", "Paris"]
        print(f"🐛 DEBUG: Cities to process: {self.cities}")
        
    def fetch_weather_data(self, city: str) -> Optional[Dict]:
        """Fetch current weather data for a city"""
        print(f"🐛 DEBUG: Fetching data for {city}...")
        try:
            # Mock data for demo
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
            print(f"🐛 DEBUG: Got data for {city}: temp={mock_data['main']['temp']}°C")
            return mock_data
            
        except Exception as e:
            print(f"🐛 DEBUG: Error fetching data for {city}: {e}")
            return None
    
    def process_weather_data(self) -> List[Dict]:
        """Process weather data for multiple cities"""
        print("🐛 DEBUG: Processing weather data...")
        data = []
        
        for city in self.cities:
            print(f"🐛 DEBUG: Processing {city}...")
            weather = self.fetch_weather_data(city)
            if weather:
                processed_item = {
                    "City": weather["name"],
                    "Temperature (°C)": weather["main"]["temp"],
                    "Humidity (%)": weather["main"]["humidity"],
                    "Pressure (hPa)": weather["main"]["pressure"],
                    "Wind Speed (m/s)": weather["wind"]["speed"],
                    "Description": weather["weather"][0]["description"],
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                data.append(processed_item)
                print(f"🐛 DEBUG: Added {city} to data list")
        
        print(f"🐛 DEBUG: Processed {len(data)} cities successfully")
        return data

    def create_simple_chart(self, data: List[Dict]):
        """Create a simple text-based chart"""
        print("🐛 DEBUG: Creating simple chart...")
        print("\n" + "="*60)
        print("📊 TEMPERATURE CHART")
        print("="*60)
        
        # Find max temp for scaling
        max_temp = max(item["Temperature (°C)"] for item in data)
        scale = 50 / max_temp if max_temp > 0 else 1
        
        for item in data:
            temp = item["Temperature (°C)"]
            bar_length = int(temp * scale)
            bar = "█" * bar_length
            print(f"{item['City']:<12} │{bar:<50}│ {temp:.1f}°C")
        
        print("="*60)
    
    def save_data(self, data: List[Dict]):
        """Save data to multiple formats"""
        print("🐛 DEBUG: Saving data...")
        
        # Save as CSV
        if data:
            try:
                with open("weather_data.csv", "w", newline="", encoding="utf-8") as csvfile:
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
                print("✅ Data saved to weather_data.csv")
            except Exception as e:
                print(f"❌ Error saving CSV: {e}")
        
        # Save as JSON
        try:
            with open("weather_data.json", "w", encoding="utf-8") as jsonfile:
                json.dump(data, jsonfile, indent=2)
            print("✅ Data saved to weather_data.json")
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")
    
    def display_summary(self, data: List[Dict]):
        """Display data summary"""
        print("🐛 DEBUG: Displaying summary...")
        
        if not data:
            print("❌ No data to display")
            return
            
        print("\n" + "="*50)
        print("WEATHER DASHBOARD SUMMARY")
        print("="*50)
        
        print(f"\nData collected at: {data[0]['Timestamp']}")
        print(f"Cities analyzed: {len(data)}")
        
        # Calculate statistics
        temps = [item["Temperature (°C)"] for item in data]
        humidity = [item["Humidity (%)"] for item in data]
        pressure = [item["Pressure (hPa)"] for item in data]
        wind = [item["Wind Speed (m/s)"] for item in data]
        
        print("\n📊 STATISTICS:")
        print(f"Average Temperature: {sum(temps)/len(temps):.1f}°C")
        print(f"Average Humidity: {sum(humidity)/len(humidity):.1f}%")
        print(f"Average Pressure: {sum(pressure)/len(pressure):.1f} hPa")
        print(f"Average Wind Speed: {sum(wind)/len(wind):.1f} m/s")
        
        print("\n🌡️ TEMPERATURE EXTREMES:")
        hottest = max(data, key=lambda x: x["Temperature (°C)"])
        coldest = min(data, key=lambda x: x["Temperature (°C)"])
        print(f"Hottest: {hottest['City']} ({hottest['Temperature (°C)']}°C)")
        print(f"Coldest: {coldest['City']} ({coldest['Temperature (°C)']}°C)")
        
        print("\n📋 DETAILED DATA:")
        print(f"{'City':<12} {'Temp(°C)':<8} {'Humidity(%)':<12} {'Pressure(hPa)':<14} {'Wind(m/s)':<10} {'Description'}")
        print("-" * 80)
        for item in data:
            print(f"{item['City']:<12} {item['Temperature (°C)']:<8.1f} "
                  f"{item['Humidity (%)']:<12} {item['Pressure (hPa)']:<14} "
                  f"{item['Wind Speed (m/s)']:<10.1f} {item['Description']}")
    
    def run(self):
        """Main application runner"""
        print("🐛 DEBUG: Starting run() method...")
        print("🌤️  Weather Dashboard Starting...")
        print("Fetching weather data...")
        
        # Process data
        data = self.process_weather_data()
        
        if not data:
            print("❌ No weather data available")
            return
        
        print("🐛 DEBUG: Data processing complete, displaying summary...")
        # Display summary
        self.display_summary(data)
        
        # Create simple visualization
        print("\n📈 Creating text-based chart...")
        self.create_simple_chart(data)
        
        # Save data
        print("\n💾 Saving data...")
        self.save_data(data)
        
        print("\n✅ Weather Dashboard Complete!")

def main():
    """Main function"""
    try:
        print("🐛 DEBUG: Entering main() function...")
        dashboard = WeatherDashboard()
        print("🐛 DEBUG: Dashboard created, calling run()...")
        dashboard.run()
        print("🐛 DEBUG: Dashboard run complete!")
    except Exception as e:
        print(f"❌ Error running application: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🐛 DEBUG: Application finishing...")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    print("🐛 DEBUG: Script started, calling main()...")
    main()
    print("🐛 DEBUG: Script complete!")