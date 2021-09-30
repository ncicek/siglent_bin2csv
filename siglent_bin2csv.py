import struct
import numpy as np

class siglent_bin2csv:
    MODEL = "SDS2000X+"
    HORI_NUM = 10
    CODE_PER_DIV ={ "SDS6000H12Pro":425,
                    "SDS5000X":30,
                    "SDS2000X+":30}

    BIT = { "SDS6000H12Pro":12,
            "SDS5000X":8,
            "SDS2000X+":8}

    def __init__(self, sds):
        self.sds = sds

    def main_desc(self, recv):
        WAVE_ARRAY_1 = recv[0x3c:0x3f+1]
        wave_array_count = recv[0x74:0x77+1]
        first_point = recv[0x84:0x87+1]
        sp = recv[0x88:0x8b+1]
        v_scale = recv[0x9c:0x9f+1]
        v_offset = recv[0xa0:0xa3+1]
        interval = recv[0xb0:0xb3+1]
        delay = recv[0xb4:0xbb+1]
        tdiv = recv[0x144:0x145+1]
        probe = recv[0x148:0x14b+1]

        tdiv_enum=[200e-12,500e-12,\
            1e-9,2e-9,5e-9,10e-9,20e-9,50e-9,100e-9,200e-9,500e-9,\
            1e-6,2e-6,5e-6,10e-6,20e-6,50e-6,100e-6,200e-6,500e-6,\
            1e-3,2e-3,5e-3,10e-3,20e-3,50e-3,100e-3,200e-3,500e-3,\
            1,2,5,10,20,50,100,200,500,1000]
        probe_enum=[0.1,0.2,0.5,1,2,5,10,20,50,100,200,500,1e3,2e3,5e3,10e3,\
            "CUSTA","CUSTB","CUSTC","CUSTD"]

        data_bytes = struct.unpack('i',WAVE_ARRAY_1)[0]
        point_num = struct.unpack('i',wave_array_count)[0]
        fp = struct.unpack('i',first_point)[0]
        sp = struct.unpack('i',sp)[0]
        interval = struct.unpack('f',interval)[0]
        delay = struct.unpack('d',delay)[0]
        tdiv_index = struct.unpack('h',tdiv)[0]
        probe_index = struct.unpack('i',probe)[0]

        if probe_index > 15:
            probe = struct.unpack('f',probe)[0]
        else:
            probe = probe_enum[probe_index]
        vdiv = struct.unpack('f',v_scale)[0]*probe
        offset = struct.unpack('f',v_offset)[0]*probe
        tdiv = tdiv_enum[tdiv_index]
        return vdiv,offset,interval,delay,tdiv,point_num

    def get_trace(self, channel):
        assert 1 <= channel <= 4
        self.sds.timeout = 5000 #default value is 2000(2s)
        self.sds.chunk_size = 10*1024*1024 #default value is 20*1024(20k bytes)
        self.sds.write("WAV:SOUR C"+str(channel))
        self.sds.write("WAV:PREamble?")
        recv = self.sds.read_raw()[16:]
        vdiv,ofst,interval,trdl,tdiv,point_num = self.main_desc(recv)
        if self.BIT[self.MODEL] > 8:
            self.sds.write(":WAVeform:WIDTh WORD")
        max_points = int(self.sds.query("WAVeform:MAXPoint?"))
        self.sds.write("WAV:POINt "+str(max_points))
        
        received_points = 0
        recv = np.empty(point_num)
        while received_points < point_num:
            self.sds.write("WAV:STARt "+str(received_points))
            self.sds.write("WAV:DATA?")
            received_data = list(self.sds.read_raw())[16:-2]
            recv[received_points : received_points + len(received_data)] = np.array(received_data)
            received_points += len(received_data)

        if self.BIT[self.MODEL] > 8:
            for i in range(0, int(len(recv) / 2)):
                data_16bit = recv[2 * i] + recv[2 * i + 1]* 256
                data = data_16bit >> (16-self.BIT[self.MODEL])
                convert_data[i] = data
        else:
            convert_data = np.array(recv)

        volt_value = np.where(convert_data > pow(2,self.BIT[self.MODEL]-1)-1, convert_data - pow(2,self.BIT[self.MODEL]), convert_data)
        volt_value = volt_value / self.CODE_PER_DIV[self.MODEL] * float(vdiv) - float(ofst)
        time_value = -float(trdl) - (float(tdiv) * self.HORI_NUM / 2) + np.arange(0, len(volt_value)) * interval
        return (time_value, volt_value)

if __name__=='__main__':
    import pyvisa as visa

    SDS_RSC = "TCPIP0::192.168.1.39::inst0::INSTR"
    sds = visa.ResourceManager().open_resource(SDS_RSC)
    
    bin2csv = siglent_bin2csv(sds)
    time, voltage = bin2csv.get_trace(4)

    