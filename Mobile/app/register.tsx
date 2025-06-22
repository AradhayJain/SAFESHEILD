import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';

export default function RegisterScreen() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [password, setPassword] = useState('');

  const handleRegister = () => {
    // Add registration logic here
    Alert.alert('Success', 'Registration complete! Please log in.');
    router.replace('/login');
  };

  return (
    <View style={styles.container}>
      <View style={styles.center}>
        <View style={styles.iconBox}>
          <MaterialCommunityIcons name="account-plus-outline" size={40} color="#2CC7A6" />
        </View>
        <Text style={styles.title}>Register</Text>
        <TextInput
          style={styles.input}
          placeholder="Username"
          value={username}
          onChangeText={setUsername}
          autoCapitalize="none"
        />
        <TextInput
          style={styles.input}
          placeholder="Account Number"
          value={accountNumber}
          onChangeText={setAccountNumber}
          keyboardType="number-pad"
          maxLength={18}
        />
        <TextInput
          style={styles.input}
          placeholder="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        <TouchableOpacity style={styles.button} onPress={handleRegister}>
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
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f7fafd' },
  center: { width: '90%', alignItems: 'center' },
  iconBox: { backgroundColor: '#e5f9f5', borderRadius: 30, padding: 16, marginBottom: 16 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#244A85', marginBottom: 16 },
  input: { width: 280, backgroundColor: '#fff', borderRadius: 8, padding: 12, fontSize: 16, borderWidth: 1, borderColor: '#e0e0e0', marginBottom: 14 },
  button: { backgroundColor: '#2CC7A6', borderRadius: 8, paddingVertical: 14, width: 280, alignItems: 'center', marginTop: 8 },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  loginBtn: { marginTop: 12, alignItems: 'center', width: 280, padding: 10, borderRadius: 8, borderWidth: 1, borderColor: '#2CC7A6', backgroundColor: '#e5f9f5' },
  loginBtnText: { color: '#244A85', fontSize: 16, fontWeight: 'bold' },
});