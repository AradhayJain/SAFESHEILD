import React, { useRef, useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, Alert, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';
import { GestureHandlerRootView, PanGestureHandler, PanGestureHandlerGestureEvent } from 'react-native-gesture-handler';

export default function RegisterScreen() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [AccountNumber, setAccountNumber] = useState('');
  const [PhoneNumber, setPhoneNumber] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const [typingTimes, setTypingTimes] = useState<number[]>([]);
  const [lastTypeTime, setLastTypeTime] = useState<number | null>(null);

  const [swipeSpeeds, setSwipeSpeeds] = useState<number[]>([]);
  const [swipeAngles, setSwipeAngles] = useState<number[]>([]);

  // Arrays to record stats after each field
  const [typingStats, setTypingStats] = useState<{mean: number, std: number}[]>([]);
  const [swipeSpeedStats, setSwipeSpeedStats] = useState<{mean: number, std: number}[]>([]);
  const [swipeAngleStats, setSwipeAngleStats] = useState<{mean: number, std: number}[]>([]);

  const scrollRef = useRef<ScrollView>(null);

  // Typing speed tracking
  const handleTyping = (setter: (v: string) => void) => (text: string) => {
    const now = Date.now();
    if (lastTypeTime !== null) {
      setTypingTimes(prev => [...prev, now - lastTypeTime]);
    }
    setLastTypeTime(now);
    setter(text);
  };

  // Utility functions
  const mean = (arr: number[]) => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
  const std = (arr: number[]) => {
    const m = mean(arr);
    return arr.length ? Math.sqrt(arr.reduce((a, b) => a + (b - m) ** 2, 0) / arr.length) : 0;
  };

  // Call this after each field is completed (onBlur)
  const recordStats = () => {
    setTypingStats(prev => [...prev, { mean: mean(typingTimes), std: std(typingTimes) }]);
    setSwipeSpeedStats(prev => [...prev, { mean: mean(swipeSpeeds), std: std(swipeSpeeds) }]);
    setSwipeAngleStats(prev => [...prev, { mean: mean(swipeAngles), std: std(swipeAngles) }]);
    setTypingTimes([]);
    setSwipeSpeeds([]);
    setSwipeAngles([]);
    setLastTypeTime(null);
  };

  // Password validation function
  const passwordCriteria = [
    { label: 'At least 6 characters', test: (pw: string) => pw.length >= 6 },
    { label: 'At least 1 special character', test: (pw: string) => /[^A-Za-z0-9]/.test(pw) },
    { label: 'At least 1 uppercase letter', test: (pw: string) => /[A-Z]/.test(pw) },
    { label: 'At least 1 lowercase letter', test: (pw: string) => /[a-z]/.test(pw) },
    { label: 'At least 1 number', test: (pw: string) => /\d/.test(pw) },
  ];

  const isPasswordValid = (pw: string) => passwordCriteria.every(c => c.test(pw));

  const handleRegister = async () => {
    if (!username || !AccountNumber || !PhoneNumber || !password || !confirmPassword) {
      Alert.alert('Error', 'Please fill all fields.');
      return;
    }
    if (!isPasswordValid(password)) {
      Alert.alert('Error', 'Password does not meet the required criteria.');
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match.');
      return;
    }
    try {
      const response = await axios.post('https://back-s4p9.onrender.com/api/users/register', {
        username,
        AccountNumber,
        PhoneNumber,
        password,
      });
      if (response.data) {
        Alert.alert(
          'Success',
          'Successfully registered! Please proceed to the next step for behaviour tracking.',
          [
            {
              text: 'OK',
              onPress: () => router.replace('/track_behaviour' as any),
            },
          ]
        );
        return;
      } else {
        Alert.alert('Registration Failed', response.data?.message || 'Please try again.');
      }
    } catch (error: any) {
      Alert.alert('Error!', error.response?.data?.message || 'Something went wrong');
    }
  };

  // Focus handlers to scroll to input
  const scrollToInput = (inputY: number) => {
    setTimeout(() => {
      scrollRef.current?.scrollTo({ y: inputY - 40, animated: true });
    }, 300);
  };

  // refs for each input
  const confirmPasswordRef = useRef<TextInput>(null);

  // Gesture tracking state
  const gestureStart = useRef<{x: number, y: number, t: number} | null>(null);

  // PanGestureHandler event
  const onGestureEvent = (event: PanGestureHandlerGestureEvent) => {
    // No-op: we only care about start and end
  };

  const onHandlerStateChange = (event: PanGestureHandlerGestureEvent) => {
    const { nativeEvent } = event;
    if (nativeEvent.state === 2) { // BEGAN
      gestureStart.current = { x: nativeEvent.x, y: nativeEvent.y, t: Date.now() };
    }
    if (nativeEvent.state === 5 && gestureStart.current) { // END
      const dx = nativeEvent.x - gestureStart.current.x;
      const dy = nativeEvent.y - gestureStart.current.y;
      const dt = Date.now() - gestureStart.current.t;
      const distance = Math.sqrt(dx * dx + dy * dy);
      if (dt > 0 && distance > 10) {
        const speed = distance / dt;
        const angle = Math.atan2(dy, dx) * (180 / Math.PI);
        setSwipeSpeeds(prev => [...prev, speed]);
        setSwipeAngles(prev => [...prev, angle]);
      }
      gestureStart.current = null;
    }
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 60 : 0}
      >
        <PanGestureHandler
          onGestureEvent={onGestureEvent}
          onHandlerStateChange={onHandlerStateChange}
        >
          <ScrollView
            ref={scrollRef}
            contentContainerStyle={styles.scrollContainer}
            keyboardShouldPersistTaps="handled"
          >
            <View style={styles.container}>
              <View style={styles.center}>
                <View style={styles.iconBox}>
                  <MaterialCommunityIcons name="account-plus-outline" size={40} color="#2CC7A6" />
                </View>
                <Text style={styles.title}>Register</Text>
                {/* Username */}
                <TextInput
                  style={styles.input}
                  placeholder="Username"
                  value={username}
                  onChangeText={handleTyping(setUsername)}
                  autoCapitalize="none"
                  onFocus={e => scrollToInput(e.nativeEvent.target)}
                  onBlur={recordStats}
                />
                {/* Account Number */}
                <TextInput
                  style={styles.input}
                  placeholder="Account Number"
                  value={AccountNumber}
                  onChangeText={handleTyping(setAccountNumber)}
                  keyboardType="number-pad"
                  maxLength={18}
                  onFocus={e => scrollToInput(e.nativeEvent.target)}
                  onBlur={recordStats}
                />
                {/* Phone Number */}
                <TextInput
                  style={styles.input}
                  placeholder="Phone Number"
                  value={PhoneNumber}
                  onChangeText={handleTyping(setPhoneNumber)}
                  keyboardType="phone-pad"
                  maxLength={10}
                  onFocus={e => scrollToInput(e.nativeEvent.target)}
                  onBlur={recordStats}
                />
                {/* Password */}
                <View style={{ width: 280, flexDirection: 'row', alignItems: 'center', marginBottom: 0 }}>
                  <TextInput
                    style={[styles.input, { flex: 1, marginBottom: 0 }]}
                    placeholder="Password"
                    value={password}
                    onChangeText={handleTyping(setPassword)}
                    secureTextEntry={!showPassword}
                    onFocus={e => scrollToInput(e.nativeEvent.target)}
                    onBlur={recordStats}
                  />
                  <TouchableOpacity onPress={() => setShowPassword(!showPassword)} style={{ position: 'absolute', right: 10 }}>
                    <MaterialCommunityIcons
                      name={showPassword ? "eye-off-outline" : "eye-outline"}
                      size={24}
                      color="#888"
                    />
                  </TouchableOpacity>
                </View>
                <View style={{ width: 280, marginBottom: 14 }}>
                  <Text
                    style={{
                      fontSize: 12,
                      color: isPasswordValid(password) ? '#2CC7A6' : '#b0b0b0',
                      marginBottom: 2,
                    }}
                  >
                    Password must be at least 6 characters, include 1 special character, 1 uppercase, 1 lowercase, and 1 number.
                  </Text>
                </View>
                {/* Confirm Password */}
                <TextInput
                  ref={confirmPasswordRef}
                  style={styles.input}
                  placeholder="Confirm Password"
                  value={confirmPassword}
                  onChangeText={handleTyping(setConfirmPassword)}
                  secureTextEntry={!showPassword}
                  onFocus={e => scrollToInput(e.nativeEvent.target)}
                  onBlur={recordStats}
                />

                {/* Show stats for debugging */}
                <Text style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>
                  Typing speed (ms): mean={mean(typingTimes).toFixed(2)}, std={std(typingTimes).toFixed(2)}
                </Text>
                <Text style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>
                  Swipe speed (px/ms): mean={mean(swipeSpeeds).toFixed(4)}, std={std(swipeSpeeds).toFixed(4)}
                </Text>
                <Text style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>
                  Swipe angle (deg): mean={mean(swipeAngles).toFixed(2)}, std={std(swipeAngles).toFixed(2)}
                </Text>
                {/* Show arrays for debugging */}
                <Text style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>
                  Typing stats array: {JSON.stringify(typingStats)}
                </Text>
                <Text style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>
                  Swipe speed stats array: {JSON.stringify(swipeSpeedStats)}
                </Text>
                <Text style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>
                  Swipe angle stats array: {JSON.stringify(swipeAngleStats)}
                </Text>
                <TouchableOpacity style={styles.swipeButton} onPress={handleRegister}>
                  <Text style={styles.buttonText}>Register</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.loginBtn}
                  onPress={() => router.replace('/login')}
                >
                  <Text style={styles.loginBtnText}>Already have an account? Login</Text>
                </TouchableOpacity>
              </View>
            </View>
          </ScrollView>
        </PanGestureHandler>
      </KeyboardAvoidingView>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  scrollContainer: { flexGrow: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f7fafd' },
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f7fafd' },
  center: { width: '90%', alignItems: 'center' },
  iconBox: { backgroundColor: '#e5f9f5', borderRadius: 30, padding: 16, marginBottom: 16 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#244A85', marginBottom: 16 },
  input: { width: 280, backgroundColor: '#fff', borderRadius: 8, padding: 12, fontSize: 16, borderWidth: 1, borderColor: '#e0e0e0', marginBottom: 14 },
  swipeButton: { backgroundColor: '#2CC7A6', borderRadius: 8, paddingVertical: 14, width: 280, alignItems: 'center', marginTop: 8, marginBottom: 8 },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  loginBtn: { marginTop: 12, alignItems: 'center', width: 280, padding: 10, borderRadius: 8, borderWidth: 1, borderColor: '#2CC7A6', backgroundColor: '#e5f9f5' },
  loginBtnText: { color: '#244A85', fontSize: 16, fontWeight: 'bold' },
});