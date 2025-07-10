import AsyncStorage from '@react-native-async-storage/async-storage';

import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';
import { useContext } from 'react';

export default function LoginScreen() {
  const [accountNumber, setAccountNumber] = useState('');
  const [password, setPassword] = useState('');
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(false);
  const router = useRouter();


  const handleLogin = async () => {
  if (!accountNumber || !password) {
    Alert.alert('Error', 'Please enter both account number and password.');
    return;
  }

  setLoading(true);
  try {
    const response = await axios.post('http://localhost:9001/api/users/login', {
      AccountNumber: accountNumber,
      password,
    });

    const { token, user } = response.data;

    if (token && user) {
      // Store token and user in AsyncStorage
      await AsyncStorage.setItem('authToken', token);
      await AsyncStorage.setItem('authUser', JSON.stringify(user));

      // Navigate only if storage succeeded
      router.replace('/main');
    } else {
      Alert.alert('Login Failed', 'Invalid credentials');
    }
  } catch (error: any) {
    console.log('Login error:', error);
    if (error.response?.status === 401) {
      Alert.alert('Login Failed', 'Invalid credentials');
    } else {
      Alert.alert('Error', error.response?.data?.message || 'Something went wrong');
    }
  } finally {
    setLoading(false);
  }
};

  return (
    <View style={styles.container}>
      <View style={styles.center}>
        <View style={styles.iconBox}>
          <MaterialCommunityIcons name="shield-outline" size={40} color="#2CC7A6" />
        </View>
        <Text style={styles.title}>Welcome Back</Text>
        <Text style={styles.subtitle}>SafeShield is learning your behavior</Text>
        <TextInput
          style={styles.input}
          placeholder="Account Number"
          value={accountNumber}
          onChangeText={setAccountNumber}
          keyboardType="number-pad"
          autoCapitalize="none"
        />
        <View style={styles.passwordContainer}>
          <TextInput
            style={styles.inputPassword}
            placeholder="Password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry={!show}
          />
          <TouchableOpacity onPress={() => setShow(!show)} style={styles.eyeIcon}>
            <MaterialCommunityIcons name={show ? "eye-off-outline" : "eye-outline"} size={22} color="#b0b0b0" />
          </TouchableOpacity>
        </View>
        <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={loading}>
          <Text style={styles.buttonText}>{loading ? 'Signing In...' : 'Sign In'}</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.firstTimeBtn}
          onPress={() => router.replace('/permission')}
        >
          <Text style={styles.firstTimeBtnText}>First time user? Register</Text>
        </TouchableOpacity>
        <View style={styles.infoRow}>
          <MaterialCommunityIcons name="lock-outline" size={16} color="#b0b0b0" />
          <Text style={styles.info}> SafeShield is invisibly authenticating your behavior</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f7fafd', justifyContent: 'center' },
  center: { alignItems: 'center', marginHorizontal: 32 },
  iconBox: { backgroundColor: '#e5f1ff', borderRadius: 16, padding: 16, marginBottom: 16 },
  title: { fontSize: 28, fontWeight: 'bold', marginBottom: 6, color: '#244A85' },
  subtitle: { fontSize: 15, color: '#244A85', marginBottom: 24 },
  input: { width: 280, backgroundColor: '#fff', borderRadius: 8, padding: 14, marginBottom: 12, fontSize: 16, borderWidth: 1, borderColor: '#e0e0e0' },
  passwordContainer: { flexDirection: 'row', alignItems: 'center', width: 280, backgroundColor: '#fff', borderRadius: 8, borderWidth: 1, borderColor: '#e0e0e0', marginBottom: 12 },
  inputPassword: { flex: 1, padding: 14, fontSize: 16 },
  eyeIcon: { paddingHorizontal: 8 },
  button: { backgroundColor: '#2CC7A6', borderRadius: 8, padding: 14, alignItems: 'center', width: 280, marginTop: 12 },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  firstTimeBtn: {
    marginTop: 10,
    alignItems: 'center',
    width: 280,
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#2CC7A6',
    backgroundColor: '#e5f9f5',
  },
  firstTimeBtnText: {
    color: '#244A85',
    fontSize: 16,
    fontWeight: '500',
  },
  infoRow: { flexDirection: 'row', alignItems: 'center', marginTop: 18 },
  info: { color: '#b0b0b0', fontSize: 13, textAlign: 'center' },
});