import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Feather, MaterialIcons } from '@expo/vector-icons';

export default function SendScreen() {
  const router = useRouter();
  const [upi, setUpi] = useState('');
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');

  const handleSendMoney = () => {
    if (!upi || !amount) {
      Alert.alert('Error', 'Please enter UPI ID and amount.');
      return;
    }
    Alert.alert('Success', 'Money successfully sent!');
    setUpi('');
    setAmount('');
    setNote('');
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: '#f7fafd' }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <View style={styles.container}>
        {/* Back Button */}
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Feather name="arrow-left" size={24} color="#244A85" />
          <Text style={styles.backText}>Back</Text>
        </TouchableOpacity>

        {/* UPI/Mobile Input */}
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            placeholder="Mobile number or UPI ID"
            value={upi}
            onChangeText={setUpi}
            keyboardType="default"
            autoCapitalize="none"
          />
          <TouchableOpacity>
            <MaterialIcons name="arrow-forward-ios" size={22} color="#1976D2" />
          </TouchableOpacity>
        </View>

        {/* Amount Input */}
        <View style={styles.inputRow}>
          <Text style={{ marginLeft: 10 }}>
            ₹
          </Text>
          <TextInput
            style={[styles.input, { borderWidth: 0, marginLeft: 4 }]}
            placeholder="Amount"
            value={amount}
            onChangeText={setAmount}
            keyboardType="numeric"
          />
        </View>

        {/* Note Input */}
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            placeholder="Note   Optional"
            value={note}
            onChangeText={setNote}
          />
        </View>

        {/* Send Money Button */}
        <TouchableOpacity style={styles.sendBtn} onPress={handleSendMoney}>
          <Text style={styles.sendBtnText}>Send Money</Text>
        </TouchableOpacity>

        {/* Info Text */}
        <Text style={styles.infoText}>
          You’ll be asked to enter your UPI PIN to confirm
        </Text>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 60,
    paddingHorizontal: 18,
    backgroundColor: '#f7fafd',
    alignItems: 'center',
  },
  backBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    marginBottom: 40,
  },
  backText: {
    color: '#244A85',
    fontSize: 16,
    marginLeft: 8,
    fontWeight: 'bold',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    marginBottom: 18,
    paddingHorizontal: 12,
    height: 56,
    width: '100%',
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: '#222',
    backgroundColor: 'transparent',
    borderWidth: 0,
  },
  sendBtn: {
    backgroundColor: '#1976D2',
    borderRadius: 12,
    marginTop: 18,
    width: '100%',
    height: 54,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendBtnText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  infoText: {
    color: '#888',
    fontSize: 15,
    marginTop: 18,
    textAlign: 'center',
  },
});