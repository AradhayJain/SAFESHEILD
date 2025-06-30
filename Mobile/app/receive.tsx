import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { Feather } from '@expo/vector-icons';

export default function ReceiveScreen() {
  const router = useRouter();
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: '#f7fafd' }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <View style={styles.container}>
        {/* Back Button */}
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Feather name="arrow-left" size={26} color="#222" />
        </TouchableOpacity>

        {/* Heading */}
        <Text style={styles.heading}>Receive Money</Text>

        {/* Amount Input */}
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
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
            placeholder="Note (Optional)"
            value={note}
            onChangeText={setNote}
          />
        </View>

        {/* Receive Money Button */}
        <TouchableOpacity style={styles.receiveBtn}>
          <Text style={styles.receiveBtnText}>Receive Money</Text>
        </TouchableOpacity>

        {/* Info Text */}
        <Text style={styles.infoText}>
          Share your UPI ID to receive payments
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
    alignSelf: 'flex-start',
    marginBottom: 18,
    marginLeft: -6,
  },
  heading: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#222',
    marginBottom: 36,
    alignSelf: 'center',
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
  receiveBtn: {
    backgroundColor: '#1976D2',
    borderRadius: 12,
    marginTop: 8,
    width: '100%',
    height: 54,
    alignItems: 'center',
    justifyContent: 'center',
  },
  receiveBtnText: {
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