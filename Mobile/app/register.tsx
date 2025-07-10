import React, { useRef, useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, Alert, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';

export default function RegisterScreen() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [AccountNumber, setAccountNumber] = useState('');
  const [PhoneNumber, setPhoneNumber] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const confirmPasswordRef = useRef<TextInput>(null);
  const scrollRef = useRef<ScrollView>(null);

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
          'Successfully registered! Please proceed to the next step.',
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

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 60 : 0}
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
              onChangeText={setUsername}
              autoCapitalize="none"
              onFocus={e => scrollToInput(e.nativeEvent.target)}
            />
            {/* Account Number */}
            <TextInput
              style={styles.input}
              placeholder="Account Number"
              value={AccountNumber}
              onChangeText={setAccountNumber}
              keyboardType="number-pad"
              maxLength={18}
              onFocus={e => scrollToInput(e.nativeEvent.target)}
            />
            {/* Phone Number */}
            <TextInput
              style={styles.input}
              placeholder="Phone Number"
              value={PhoneNumber}
              onChangeText={setPhoneNumber}
              keyboardType="phone-pad"
              maxLength={10}
              onFocus={e => scrollToInput(e.nativeEvent.target)}
            />
            {/* Password */}
            <View style={{ width: 280, flexDirection: 'row', alignItems: 'center', marginBottom: 0 }}>
              <TextInput
                style={[styles.input, { flex: 1, marginBottom: 0 }]}
                placeholder="Password"
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPassword}
                onFocus={e => scrollToInput(e.nativeEvent.target)}
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
              onChangeText={setConfirmPassword}
              secureTextEntry={!showPassword}
              onFocus={e => scrollToInput(e.nativeEvent.target)}
            />

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
    </KeyboardAvoidingView>
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