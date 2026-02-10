"""
🎯 Safe Kids Data Generator - النسخة النهائية
100 طفل | 7 أيام | 7% حوادث | 55% تحرش
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# ====================================
# 1️⃣ توليد معدل النبض
# ====================================

def generate_heart_rate(age, hour, condition):
    if age <= 6:
        base_hr = 95
    elif age <= 9:
        base_hr = 85
    else:
        base_hr = 80
    
    if 0 <= hour < 6:
        time_adjustment = -10
    elif 6 <= hour < 8:
        time_adjustment = 0
    elif 8 <= hour < 12:
        time_adjustment = 5
    elif 12 <= hour < 14:
        time_adjustment = 12
    elif 14 <= hour < 15:
        time_adjustment = 5
    elif 15 <= hour < 18:
        time_adjustment = 15
    elif 18 <= hour < 21:
        time_adjustment = 5
    else:
        time_adjustment = -5
    
    if condition == 'adhd':
        condition_adjustment = 5
    elif condition == 'autism':
        condition_adjustment = random.randint(-3, 7)
    else:
        condition_adjustment = 0
    
    noise = random.gauss(0, 3)
    final_hr = base_hr + time_adjustment + condition_adjustment + noise
    
    return max(60, min(200, int(final_hr)))


# ====================================
# 2️⃣ توليد مستوى النشاط
# ====================================

def generate_activity_level(hour, condition):
    if 0 <= hour < 6:
        base_activity = 5
    elif 6 <= hour < 8:
        base_activity = 20
    elif 8 <= hour < 12:
        base_activity = 30
    elif 12 <= hour < 14:
        base_activity = 65
    elif 14 <= hour < 15:
        base_activity = 30
    elif 15 <= hour < 18:
        base_activity = 70
    elif 18 <= hour < 21:
        base_activity = 40
    else:
        base_activity = 20
    
    if condition == 'adhd':
        base_activity += random.randint(10, 25)
    
    noise = random.randint(-10, 10)
    final_activity = base_activity + noise
    
    return max(0, min(100, final_activity))


# ====================================
# 3️⃣ توليد الموقع
# ====================================

def generate_location(hour):
    base_lat = 30.0444
    base_lon = 31.2357
    
    if 0 <= hour < 7:
        location_name = "المنزل"
        lat = base_lat
        lon = base_lon
    elif 7 <= hour < 8:
        location_name = "في الطريق"
        lat = base_lat + 0.01
        lon = base_lon + 0.01
    elif 8 <= hour < 15:
        location_name = "المدرسة"
        lat = base_lat + 0.02
        lon = base_lon + 0.02
    elif 15 <= hour < 16:
        location_name = "في الطريق"
        lat = base_lat + 0.01
        lon = base_lon + 0.01
    elif 16 <= hour < 19:
        location_name = "النادي"
        lat = base_lat - 0.01
        lon = base_lon - 0.01
    else:
        location_name = "المنزل"
        lat = base_lat
        lon = base_lon
    
    lat += random.uniform(-0.0001, 0.0001)
    lon += random.uniform(-0.0001, 0.0001)
    
    return location_name, round(lat, 6), round(lon, 6)


# ====================================
# 4️⃣ إضافة حوادث (7% - 55% تحرش)
# ====================================

def add_incident(base_hr, base_activity):
    """
    7% احتمال حدوث حادث
    55% منها تحرش/خطر
    """
    if random.random() < 0.07:  # ← 7%
        
        # التوزيع: 55% تحرش، 25% قلق، 15% رياضة، 5% سقوط
        incident_type = random.choices(
            ['potential_danger', 'anxiety_attack', 'intense_exercise', 'fall'],
            weights=[55, 25, 15, 5],  # ← 55% تحرش
            k=1
        )[0]
        
        if incident_type == 'potential_danger':
            # تحرش/خطر: قفزة كبيرة جداً
            new_hr = base_hr + random.randint(55, 75)
            new_activity = base_activity + random.randint(40, 60)
        
        elif incident_type == 'anxiety_attack':
            # نوبة قلق
            new_hr = base_hr + random.randint(45, 65)
            new_activity = base_activity + random.randint(35, 55)
        
        elif incident_type == 'intense_exercise':
            # رياضة مكثفة
            new_hr = base_hr + random.randint(20, 35)
            new_activity = base_activity + random.randint(25, 35)
        
        else:  # fall
            # سقوط
            new_hr = base_hr + random.randint(30, 50)
            new_activity = 0
        
        return new_hr, new_activity, incident_type
    
    else:
        return base_hr, base_activity, 'none'


# ====================================
# 5️⃣ توليد بيانات يوم واحد (وقت الخروج فقط)
# ====================================

def generate_child_day(child_id, age, condition, date):
    """
    توليد بيانات وقت الخروج فقط
    من 7 صباحاً → 7 مساءً (12 ساعة)
    48 قراءة/يوم
    """
    readings = []
    
    # البداية: 7 صباحاً
    start_hour = 7
    end_hour = 19
    
    current_time = datetime.combine(date, datetime.min.time())
    current_time = current_time.replace(hour=start_hour)
    
    # 12 ساعة × 4 قراءات/ساعة = 48 قراءة
    num_readings = (end_hour - start_hour) * 4
    
    for _ in range(num_readings):
        hour = current_time.hour
        
        if start_hour <= hour < end_hour:
            hr = generate_heart_rate(age, hour, condition)
            activity = generate_activity_level(hour, condition)
            location_name, lat, lon = generate_location(hour)
            
            hr, activity, incident = add_incident(hr, activity)
            
            readings.append({
                'child_id': child_id,
                'timestamp': current_time,
                'age': age,
                'condition': condition,
                'heart_rate': hr,
                'activity_level': activity,
                'location': location_name,
                'latitude': lat,
                'longitude': lon,
                'incident_type': incident
            })
        
        current_time += timedelta(minutes=15)
    
    return readings


# ====================================
# 6️⃣ توليد Dataset كامل
# ====================================

def generate_full_dataset(num_children=100, num_days=7):
    """
    100 طفل × 7 أيام × 48 قراءة = 33,600 قراءة
    """
    print("=" * 60)
    print("🚀 بدء توليد البيانات...")
    print("=" * 60)
    print(f"📊 عدد الأطفال: {num_children}")
    print(f"📅 عدد الأيام لكل طفل: {num_days}")
    print(f"⏰ وقت التشغيل: 7 صباحاً - 7 مساءً")
    print(f"🔢 إجمالي القراءات المتوقعة: {num_children * num_days * 48:,}")
    print(f"🚨 نسبة الحوادث: 7% (55% منها تحرش)")
    print("=" * 60)
    print()
    
    all_data = []
    
    for child_num in range(num_children):
        child_id = f"child_{child_num:03d}"
        
        age = random.randint(5, 12)
        
        rand = random.random()
        if rand < 0.6:
            condition = 'normal'
        elif rand < 0.8:
            condition = 'autism'
        else:
            condition = 'adhd'
        
        start_date = datetime.now().date() - timedelta(days=num_days)
        
        for day_num in range(num_days):
            current_date = start_date + timedelta(days=day_num)
            day_readings = generate_child_day(child_id, age, condition, current_date)
            all_data.extend(day_readings)
        
        if (child_num + 1) % 20 == 0:
            print(f"✅ تم توليد بيانات {child_num + 1}/{num_children} طفل")
    
    print()
    print("=" * 60)
    print("🎉 اكتمل التوليد!")
    print("=" * 60)
    
    df = pd.DataFrame(all_data)
    
    print(f"📊 إجمالي القراءات: {len(df):,}")
    print(f"🧒 عدد الأطفال: {df['child_id'].nunique()}")
    print(f"📅 الفترة الزمنية: {df['timestamp'].min()} إلى {df['timestamp'].max()}")
    print()
    print("📈 توزيع الحالات:")
    print(df['condition'].value_counts())
    print()
    print("🚨 توزيع الحوادث:")
    incident_counts = df['incident_type'].value_counts()
    print(incident_counts)
    
    if 'potential_danger' in incident_counts:
        danger_percentage = (incident_counts['potential_danger'] / len(df)) * 100
        print(f"\n⚠️  نسبة حوادث التحرش/الخطر: {danger_percentage:.2f}%")
        print(f"   (عدد: {incident_counts['potential_danger']:,} حادث)")
    
    print()
    
    return df


# ====================================
# 7️⃣ حفظ البيانات (مع encoding صحيح)
# ====================================

def save_dataset(df, filename='training_data.csv'):
    """
    حفظ مع encoding='utf-8-sig' للعربي
    """
    os.makedirs('data', exist_ok=True)
    filepath = os.path.join('data', filename)
    
    # ← encoding هنا مهم جداً!
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    print("=" * 60)
    print("💾 تم الحفظ!")
    print("=" * 60)
    print(f"📂 الموقع: {filepath}")
    file_size_mb = os.path.getsize(filepath) / (1024*1024)
    print(f"💿 حجم الملف: {file_size_mb:.2f} MB")
    print("=" * 60)
    print()
    
    return filepath


# ====================================
# 8️⃣ عرض نماذج
# ====================================

def show_samples(df, num_samples=10):
    print("=" * 60)
    print("👀 عينة من البيانات:")
    print("=" * 60)
    print(df.head(num_samples))
    print()
    
    print("=" * 60)
    print("📊 الإحصائيات:")
    print("=" * 60)
    print(df[['heart_rate', 'activity_level']].describe())
    print()


# ====================================
# 9️⃣ البرنامج الرئيسي
# ====================================

def main():
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 8 + "🎯 Safe Kids Data Generator - v2.0" + " " * 15 + "║")
    print("║" + " " * 6 + "100 طفل | 7% حوادث | 55% تحرش" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # توليد
    dataset = generate_full_dataset(
        num_children=100,  # ← 100 طفل
        num_days=7
    )
    
    # عرض نماذج
    show_samples(dataset)
    
    # حفظ
    filepath = save_dataset(dataset)
    
    print("✨ تم بنجاح! ✨")
    print()
    print("📝 ملخص النتائج:")
    print(f"  • إجمالي القراءات: {len(dataset):,}")
    print(f"  • عدد الأطفال: 100")
    print(f"  • الحوادث: ~{int(len(dataset) * 0.07):,} (7%)")
    print(f"  • حوادث التحرش: ~{int(len(dataset) * 0.07 * 0.55):,}")
    print()
    print("🚀 جاهز للتحليل والتدريب!")
    print()


# ====================================
# 🎬 تشغيل
# ====================================

if __name__ == "__main__":
    main()
