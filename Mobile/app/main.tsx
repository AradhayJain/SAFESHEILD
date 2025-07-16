import React, { useEffect, useState } from 'react';
import { Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons, MaterialIcons, Feather } from '@expo/vector-icons';
import { GestureHandlerRootView, PanGestureHandler, State as GestureState } from 'react-native-gesture-handler';
import { useSocket } from '../context/SocketContext';
import { useFocusEffect } from '@react-navigation/native';
import { useCallback } from 'react';

export default function MainScreen() {
  const router = useRouter();
  const socket = useSocket();
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<any>(null);

  // Swipe data states
  const [swipeDistances, setSwipeDistances] = useState<number[]>([]);
  const [swipeDurations, setSwipeDurations] = useState<number[]>([]);
  const [swipeSpeeds, setSwipeSpeeds] = useState<number[]>([]);
  const [swipeDirections, setSwipeDirections] = useState<number[]>([]);
  const [swipeAccelerations, setSwipeAccelerations] = useState<number[]>([]);
  const [flagged, setFlagged] = useState<string[]>([]);


  // For tracking swipe
  const swipeStart = React.useRef<{ x: number; y: number; time: number } | null>(null);
  // useEffect(() => {
  //   const handlePrediction = (msg: string) => {
  //     console.log('📨 Received prediction:', msg);
  //   };
  
  //   if (!socket) return;
  
  //   const setupListeners = () => {
  //     socket.off('prediction-result', handlePrediction); // ensure no duplicate
  //     socket.on('prediction-result', handlePrediction);
  //   };
  
  //   // Attach on first connect
  //   if (socket.connected) {
  //     setupListeners();
  //   }
  
  //   // Reattach after reconnects
  //   socket.on('reconnect', setupListeners);
  //   socket.on('connect', setupListeners); // also handle delayed connect
  
  //   return () => {
  //     socket.off('prediction-result', handlePrediction);
  //     socket.off('reconnect', setupListeners);
  //     socket.off('connect', setupListeners);
  //   };
  // }, []);

useFocusEffect(
  useCallback(() => {
    const handlePrediction = (msg: string) => {
      console.log('📨 Received prediction:', msg);
              // Parse JSON string
        let data;
        try {
          data = JSON.parse(msg);
        } catch (e) {
          console.error('❌ Failed to parse prediction message:', e);
          return;
        }

        // Extract swipeRisk
        const swipeRisk = data?.swiping?.prediction_result?.risk_category;
        console.log('🧪 swipeRisk:', swipeRisk);

        if (!swipeRisk) return;

        // If critical risk → alert and logout
        if (swipeRisk === 'critical_risk') {
          Alert.alert(
            'Security Alert',
            'Critical risk detected. You will be logged out....',
          );
          router.push('/login');
          return;
        }

        // Otherwise, store risk in flagged
        setFlagged((prev) => {
          const updated = [...prev, swipeRisk];

          const mediumCount = updated.filter(
            (risk) => risk === 'medium_risk'
          ).length;
          const highCount = updated.filter(
            (risk) => risk === 'high_risk'
          ).length;
          const lowCount = updated.filter(
            (risk) => risk === 'low_risk'
          ).length;

          console.log(
            `⚠️ Risks so far → Low: ${lowCount}, Medium: ${mediumCount}, High: ${highCount}`
          );

          if (lowCount >= 10 || mediumCount >= 5 || highCount >= 2) {
            Alert.alert(
              'Security Alert',
              'Too many risky sessions detected. Logging out.....',
            );
            router.push('/login');
          }
          return updated;
        });
    };

    if (!socket) return;

    socket.on('prediction-result', handlePrediction);
    console.log("🔄 Focused MainScreen, socket ID:", socket.id);

    return () => {
      socket.off('prediction-result', handlePrediction);
      console.log("👋 Unfocused MainScreen, removed socket listener");
    };
  }, [socket])
);
  
  
   // <== ❌ DO NOT include `socket` in the dependency array
  

  const onGestureEvent = React.useCallback((event: any) => {
    // No-op, required for PanGestureHandler
  }, []);

  const onHandlerStateChange = React.useCallback((event: import('react-native-gesture-handler').PanGestureHandlerStateChangeEvent) => {
    const { state, absoluteX, absoluteY } = event.nativeEvent;
    if (state === GestureState.BEGAN) {
      swipeStart.current = { x: absoluteX, y: absoluteY, time: Date.now() };
    }
    if (state === GestureState.END && swipeStart.current) {
      const dx = absoluteX - swipeStart.current.x;
      const dy = absoluteY - swipeStart.current.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      const duration = Date.now() - swipeStart.current.time;
      const speed = duration > 0 ? distance / duration : 0;
      let direction = Math.atan2(dy, dx) * (180 / Math.PI);
      if(direction < 0) direction += 360;
      const acceleration = duration > 0 ? (1e5)*speed / duration : 0;

      setSwipeDistances((prev) => [...prev, distance]);
      setSwipeDurations((prev) => [...prev, duration]);
      setSwipeSpeeds((prev) => [...prev, speed]);
      setSwipeDirections((prev) => [...prev, direction]);
      setSwipeAccelerations((prev) => [...prev, acceleration]);

      // Only print the requested arrays to the terminal
      console.log({
        swipeDistances: [...swipeDistances, distance],
        swipeDurations: [...swipeDurations, duration],
        swipeSpeeds: [...swipeSpeeds, speed],
        swipeDirections: [...swipeDirections, direction],
        swipeAccelerations: [...swipeAccelerations, acceleration],
      });
      const swipeDistancesNew = [...swipeDistances, distance];
      const swipeDurationsNew = [...swipeDurations, duration];
      const swipeSpeedsNew = [...swipeSpeeds, speed];
      const swipeDirectionsNew = [...swipeDirections, direction];
      const swipeAccelerationsNew = [...swipeAccelerations, acceleration];
      const data = {
        swipeDistancesNew,
        swipeDurationsNew,
        swipeSpeedsNew,
        swipeDirectionsNew,
        swipeAccelerationsNew
      };
      
      if (user && user._id) {
        console.log(user)
        console.log(data)
        if(swipeDistancesNew.length > 5) {
          socket.emit('send-features', { data, user_id: user._id });
        }
  }
  
      swipeStart.current = null;
    }
  }, [swipeDistances, swipeDurations, swipeSpeeds, swipeDirections, swipeAccelerations]);

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
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PanGestureHandler
        onGestureEvent={onGestureEvent}
        onHandlerStateChange={onHandlerStateChange}
      >
        <View style={{ flex: 1 }}>
          <ScrollView
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
  container: { flex: 1, paddingHorizontal: 16, marginBottom: 0 },
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
  navBar: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#fff',
    flexDirection: 'row',
    height: 64,
    borderTopLeftRadius: 18,
    borderTopRightRadius: 18,
    elevation: 10,
    justifyContent: 'space-around',
    alignItems: 'center',
    // Remove marginBottom or paddingBottom if present
    // Add this to avoid overlap with the gesture bar on iOS:
    paddingBottom: Platform.OS === 'ios' ? 24 : 0,
  },
  navItem: { alignItems: 'center', flex: 1 },
  navLabel: { color: '#b0b0b0', fontSize: 12, marginTop: 2 },
  navLabelActive: { color: '#2CC7A6', fontWeight: 'bold', fontSize: 12, marginTop: 2 },
});