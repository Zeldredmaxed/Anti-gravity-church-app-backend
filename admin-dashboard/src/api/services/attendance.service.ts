import { apiClient } from '../client';

export interface Service {
    id: number;
    name: string;
    start_time: string;
    end_time: string;
    location: string;
}

export interface AttendanceRecord {
    id: number;
    member_id: number | null;
    member_name: string | null;
    service_id: number;
    service_name: string | null;
    date: string;
    check_in_time: string | null;
    check_out_time: string | null;
    is_first_time_guest: boolean;
    guest_info: any | null;
}

export interface AttendanceTrend {
    period: string;
    total: number;
    members: number;
    guests: number;
}

export const attendanceService = {
    getServices: async (): Promise<Service[]> => {
        const response = await apiClient.get('/api/v1/attendance/services');
        return response.data;
    },
    getServiceAttendance: async (serviceId: number, attendanceDate: string): Promise<AttendanceRecord[]> => {
        const response = await apiClient.get(`/api/v1/attendance/service/${serviceId}?attendance_date=${attendanceDate}`);
        return response.data;
    },
    getTrends: async (weeks: number = 12): Promise<AttendanceTrend[]> => {
        const response = await apiClient.get(`/api/v1/attendance/trends?weeks=${weeks}`);
        return response.data;
    },
    checkIn: async (data: { service_id: number, member_id?: number, date: string, is_first_time_guest?: boolean, guest_info?: any }): Promise<AttendanceRecord> => {
        const response = await apiClient.post('/api/v1/attendance/checkin', data);
        return response.data;
    },
    checkOut: async (attendanceRecordId: number): Promise<any> => {
        const response = await apiClient.post('/api/v1/attendance/checkout', { attendance_record_id: attendanceRecordId });
        return response.data;
    }
};
