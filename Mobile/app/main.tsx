import React, { useEffect, useState, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons, MaterialIcons, Feather } from '@expo/vector-icons';
import { BehaviourTracker } from './behaviourTracker';
import { PanGestureHandler, PanGestureHandlerGestureEvent, GestureHandlerRootView } from 'react-native-gesture-handler';

export default function MainScreen() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<any>(null);

  // Typing tracking state (for future use, no input field here)
  const keyDownTime = useRef<number | null>(null);
  const lastKeyUpTime = useRef<number | null>(null);
  const firstKeyDownTime = useRef<number | null>(null);
  const totalKeys = useRef<number>(0);
  const backspaceCount = useRef<number>(0);

  // Gesture tracking state for the swipe area
  const gestureStart = useRef<{x: number, y: number, t: number} | null>(null);

  // Ref for ScrollView to use with simultaneousHandlers
  const scrollRef = useRef(null);

  useEffect(() => {
    const loadStoredData = async () => {
      try {
        const storedToken = await AsyncStorage.getItem('authToken');
        const storedUser = await AsyncStorage.getItem('authUser');
        if (storedToken) setToken(storedToken);
        if (storedUser) setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('Error loading from AsyncStorage', error);
      }
    };

    loadStoredData();

    // Print tracked behaviour data to console on mount
    BehaviourTracker.getAll().then(data => {
      console.log('Tracked Behaviour Data:', data);
    });
  }, []);

  // --- Gesture tracking for the entire screen ---
  const onGestureEvent = (event: PanGestureHandlerGestureEvent) => {
    // No-op
  };

  const onHandlerStateChange = (event: PanGestureHandlerGestureEvent) => {
    const { nativeEvent } = event;
    if (nativeEvent.state === 2) { // BEGAN
      gestureStart.current = { x: nativeEvent.x, y: nativeEvent.y, t: Date.now() };
    }
    if (nativeEvent.state === 5 && gestureStart.current) { // END
      const x1 = gestureStart.current.x;
      const y1 = gestureStart.current.y;
      const t1 = gestureStart.current.t;
      const x2 = nativeEvent.x;
      const y2 = nativeEvent.y;
      const t2 = Date.now();

      const dx = x2 - x1;
      const dy = y2 - y1;
      const distance = Math.sqrt(dx * dx + dy * dy);
      const duration = t2 - t1;
      const speed = duration > 0 ? distance / duration : 0;
      const direction = Math.atan2(dy, dx);
      const acceleration = duration > 0 ? speed / duration : 0;

      // Only record if swipe is significant
      if (distance > 20 && duration > 0) {
        BehaviourTracker.addSwipeDistance(distance);
        BehaviourTracker.addSwipeDuration(duration);
        BehaviourTracker.addSwipeSpeed(speed);
        BehaviourTracker.addSwipeDirection(direction);
        BehaviourTracker.addSwipeAcceleration(acceleration);
        console.log('Swipe recorded:', { distance, duration, speed, direction, acceleration });
      }

      gestureStart.current = null;
    }
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PanGestureHandler
        onGestureEvent={onGestureEvent}
        onHandlerStateChange={onHandlerStateChange}
        simultaneousHandlers={scrollRef}
      >
        <View style={{ flex: 1 }}>
          <ScrollView
            ref={scrollRef}
            style={styles.container}
            contentContainerStyle={{ flexGrow: 1 }}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
          >
            <View style={styles.headerRow}>
              <View>
                <Text style={styles.greeting}>Good Morning, {user?.username}</Text>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                  <MaterialCommunityIcons name="shield-check-outline" size={16} color="#2CC7A6" />
                  <Text style={styles.status}> SafeShield Active </Text>
                  <Text style={styles.percent}>5.6%</Text>
                </View>
              </View>
              <View style={styles.headerIcons}>
                <Feather name="bell" size={22} color="#244A85" style={{ marginRight: 16 }} />
                <Feather name="user" size={22} color="#244A85" onPress={() => router.push('/profile')} />
              </View>
            </View>

            <View style={styles.card}>
              <Text style={styles.balanceLabel}>Total Balance</Text>
              <Text style={styles.balance}>₹24,853.42</Text>
              <Text style={styles.account}>Account: {user?.AccountNumber}</Text>
              <Text style={styles.percentCard}>+2.4%</Text>
            </View>

            <View style={styles.row}>
              <TouchableOpacity
                style={styles.actionBtn}
                onPress={() => router.push('/send' as any)}
              >
                <MaterialIcons name="arrow-upward" size={20} color="#2CC7A6" />
                <Text style={styles.actionText}>Send</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionBtn}
                onPress={() => router.push('/receive' as any)}
              >
                <MaterialIcons name="arrow-downward" size={20} color="#2CC7A6" />
                <Text style={styles.actionText}>Receive</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionBtn}
                onPress={() => router.push('/top_up' as any)}
              >
                <MaterialIcons name="add" size={20} color="#2CC7A6" />
                <Text style={styles.actionText}>Top Up</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.shieldBox}>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <MaterialCommunityIcons name="shield-outline" size={18} color="#2CC7A6" />
                <Text style={styles.shieldStatus}> SafeShield Status </Text>
                <Text style={styles.active}>• Active</Text>
              </View>
              <View style={styles.confidenceRow}>
                <View style={styles.confidenceCol}>
                  <Text style={styles.confidenceValue}>11%</Text>
                  <Text style={styles.confidenceLabel}>Touch Confidence</Text>
                </View>
                <View style={styles.confidenceCol}>
                  <Text style={styles.confidenceValue}>12%</Text>
                  <Text style={styles.confidenceLabel}>Gesture Match</Text>
                </View>
              </View>
            </View>

            <Text style={styles.sectionTitle}>Recent Activity</Text>
            <View style={styles.activityBox}>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <MaterialCommunityIcons name="bank-transfer-in" size={22} color="#2CC7A6" />
                <Text style={styles.activityTitle}> Salary Deposit</Text>
              </View>
              <Text style={styles.activityAmount}>+ $3,500.00</Text>
              <Text style={styles.activityTime}>2 hours ago • Verified</Text>
            </View>
            <View style={styles.activityBox}>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <MaterialCommunityIcons name="coffee" size={22} color="#e74c3c" />
                <Text style={styles.activityTitle}> Coffee Shop</Text>
              </View>
              <Text style={[styles.activityAmount, { color: '#e74c3c' }]}>- $4.50</Text>
              <Text style={styles.activityTime}>Yesterday • Auto-approved</Text>
            </View>

            {/* Bottom Navigation Bar */}
            <View style={styles.navBar}>
              <TouchableOpacity style={styles.navItem}>
                <MaterialCommunityIcons name="home-outline" size={24} color="#2CC7A6" />
                <Text style={styles.navLabelActive}>Home</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.navItem} onPress={() => router.push('/activity' as any)}>
                <MaterialCommunityIcons name="history" size={24} color="#b0b0b0" />
                <Text style={styles.navLabel}>Activity</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.navItem} onPress={() => router.push('/cards' as any)}>
                <MaterialCommunityIcons name="credit-card-outline" size={24} color="#b0b0b0" />
                <Text style={styles.navLabel}>Cards</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.navItem} onPress={() => router.push('/settings' as any)}>
                <MaterialCommunityIcons name="cog-outline" size={24} color="#b0b0b0" />
                <Text style={styles.navLabel}>Settings</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </View>
      </PanGestureHandler>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  outer: { flex: 1, backgroundColor: '#f7fafd' },
  container: { flex: 1, paddingHorizontal: 16, marginBottom: 70 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 32, marginBottom: 12 },
  greeting: { fontSize: 22, fontWeight: 'bold', color: '#244A85' },
  status: { fontSize: 15, color: '#244A85' },
  percent: { color: '#2CC7A6', fontWeight: 'bold' },
  headerIcons: { flexDirection: 'row', alignItems: 'center' },
  card: { backgroundColor: '#2CC7A6', borderRadius: 18, padding: 24, marginBottom: 18, elevation: 2 },
  balanceLabel: { color: '#fff', fontSize: 14, marginBottom: 6 },
  balance: { color: '#fff', fontSize: 32, fontWeight: 'bold' },
  account: { color: '#e0f7ef', fontSize: 13, marginTop: 4 },
  percentCard: { color: '#fff', fontSize: 13, marginTop: 2 },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 18 },
  actionBtn: { flex: 1, backgroundColor: '#fff', margin: 4, borderRadius: 10, padding: 14, alignItems: 'center', flexDirection: 'row', justifyContent: 'center', borderWidth: 1, borderColor: '#e0e0e0' },
  actionText: { color: '#244A85', fontWeight: 'bold', marginLeft: 6 },
  shieldBox: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 18, elevation: 1 },
  shieldStatus: { fontWeight: 'bold', color: '#244A85', marginLeft: 6 },
  active: { color: '#2CC7A6', fontWeight: 'bold', marginLeft: 6 },
  confidenceRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 12 },
  confidenceCol: { alignItems: 'center', flex: 1 },
  confidenceValue: { color: '#2CC7A6', fontWeight: 'bold', fontSize: 18 },
  confidenceLabel: { color: '#b0b0b0', fontSize: 13, marginTop: 2 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 8, color: '#244A85' },
  activityBox: { backgroundColor: '#fff', borderRadius: 10, padding: 14, marginBottom: 10, elevation: 1 },
  activityTitle: { fontWeight: 'bold', color: '#244A85', marginLeft: 6 },
  activityAmount: { color: '#2CC7A6', fontWeight: 'bold', fontSize: 16, marginTop: 4 },
  activityTime: { color: '#b0b0b0', fontSize: 12, marginTop: 2 },
  profileBtn: { backgroundColor: '#244A85', borderRadius: 8, padding: 14, alignItems: 'center', marginVertical: 24 },
  profileBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  navBar: { position: 'absolute', left: 0, right: 0, bottom: 0, backgroundColor: '#fff', flexDirection: 'row', height: 64, borderTopLeftRadius: 18, borderTopRightRadius: 18, elevation: 10, justifyContent: 'space-around', alignItems: 'center' },
  navItem: { alignItems: 'center', flex: 1 },
  navLabel: { color: '#b0b0b0', fontSize: 12, marginTop: 2 },
  navLabelActive: { color: '#2CC7A6', fontWeight: 'bold', fontSize: 12, marginTop: 2 },
});