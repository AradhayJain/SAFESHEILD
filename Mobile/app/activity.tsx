import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Feather } from '@expo/vector-icons';

export default function ActivityScreen() {
  const router = useRouter();

  // Sample transaction data
  const transactions = [
    { id: 1, type: 'Debit', amount: 2500, date: '2025-06-20', description: 'Grocery Store' },
    { id: 2, type: 'Credit', amount: 5000, date: '2025-06-19', description: 'Salary' },
    { id: 3, type: 'Debit', amount: 1200, date: '2025-06-18', description: 'Electricity Bill' },
    { id: 4, type: 'Debit', amount: 800, date: '2025-06-17', description: 'Mobile Recharge' },
    { id: 5, type: 'Credit', amount: 2000, date: '2025-06-16', description: 'Refund' },
    { id: 6, type: 'Debit', amount: 1500, date: '2025-06-15', description: 'Restaurant' },
    { id: 7, type: 'Debit', amount: 300, date: '2025-06-14', description: 'Coffee Shop' },
    { id: 8, type: 'Credit', amount: 1000, date: '2025-06-13', description: 'Gift' },
    { id: 9, type: 'Debit', amount: 4000, date: '2025-06-12', description: 'Online Shopping' },
    { id: 10, type: 'Debit', amount: 600, date: '2025-06-11', description: 'Petrol Pump' },
  ];

  return (
    <View style={styles.container}>
      <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
        <Feather name="arrow-left" size={24} color="#244A85" />
        <Text style={styles.backText}>Back</Text>
      </TouchableOpacity>
      <Text style={styles.heading}>Recent Activity</Text>
      <ScrollView style={styles.scrollView} contentContainerStyle={{ paddingBottom: 24 }}>
        <View style={styles.listContainer}>
          {transactions.map(txn => (
            <View key={txn.id} style={styles.txnItem}>
              <Text style={styles.txnDesc}>{txn.description}</Text>
              <Text style={styles.txnDate}>{txn.date}</Text>
              <Text style={[styles.txnAmount, txn.type === 'Credit' ? styles.credit : styles.debit]}>
                {txn.type === 'Credit' ? '+' : '-'}₹{txn.amount}
              </Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f7fafd', alignItems: 'center', paddingTop: 80 },
  backBtn: { flexDirection: 'row', alignItems: 'center', position: 'absolute', top: 40, left: 16, zIndex: 2 },
  backText: { marginLeft: 4, fontSize: 16, color: '#244A85' },
  heading: { fontSize: 26, fontWeight: 'bold', color: '#244A85', marginBottom: 12, marginTop: 0 },
  text: { fontSize: 24, fontWeight: 'bold', color: '#244A85', marginBottom: 24 }, // can be removed if not used
  scrollView: { width: '100%', flex: 1 },
  listContainer: { width: '90%', alignSelf: 'center', marginTop: 8 },
  txnItem: { backgroundColor: '#fff', borderRadius: 8, padding: 16, marginBottom: 12, elevation: 2 },
  txnDesc: { fontSize: 16, fontWeight: '600', color: '#244A85' },
  txnDate: { fontSize: 12, color: '#888', marginTop: 2 },
  txnAmount: { fontSize: 18, fontWeight: 'bold', marginTop: 4 },
  credit: { color: '#2ecc71' },
  debit: { color: '#e74c3c' },
});
