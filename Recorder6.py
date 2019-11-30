'''
说明：
此程序基于百度语音API、图灵机器人API，实现了语音识别、语音合成、与机器人对话的功能；

方法：
运行程序，在聊天界面点击按钮开始说话，再次点击按钮完成录音后，聊天机器人将进行符合逻辑的语音回复。
此过程中双方的语音将以文字形式显示在对话框中。

原理: 
1.调用百度语音API，对录音进行语音识别，转换为文字；
2.调用图灵机器人API，把文字交给图灵机器人处理，机器人将返回文字形式的回答；
3.再次调用百度语音API，对机器人的回答进行语音合成，并播放。
'''

import wave  # wave库 用来录音
import threading  # 多线程
import pygame  # 播放音频
from pyaudio import PyAudio, paInt16  # 录音
from tkinter import *  # GUI库
from aip import AipSpeech  # 百度语音
import json  # 机器人url请求要用的库
import urllib.request  # 机器人url请求要用的库

class Recorder(object):

    def __init__(self):
        self.num_samples = 2000    # pyaudio内置缓冲大小 CHUNK
        self.sampling_rate = 8000  # 取样频率
        self.running = True  # 初始化，开始运行
        self.frames = []  # 初始化录音帧列表
        APP_ID = '***********'
        API_KEY = '**********'
        SECRET_KEY = '*************' #百度语音API用户信息
        self.client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)  # 建立百度语音识别客户对象

    #保存文件
    def save_wav(self, filename):
        wf = wave.open(filename, 'wb')  # 打开文件
        wf.setnchannels(1)  # 单声道录音
        wf.setsampwidth(2)  # 采样宽度
        wf.setframerate(self.sampling_rate)  # 设定采样率
        wf.writeframes(b''.join(self.frames))  # 写入
        wf.close()  # 关闭文件
        print('save successful')  # 输出“录音文件保存成功”提示
    
    #录音
    def read_audio(self):
        pa = PyAudio()  # 先建立pyaudio对象
        stream = pa.open(format=paInt16, channels=1, rate=self.sampling_rate, input=True, 
                frames_per_buffer=self.num_samples)   # 开启流
        self.running = True  # 开始运行录音
        self.frames = []  # 初始化录音帧列表（添加这行代码，解决了每次启动录音时长一个接一个叠加的问题）
        while(self.running):  # 录音运行期间
            data = stream.read(self.num_samples)  # 读入数据
            self.frames.append(data)  # 加入
        stream.stop_stream()  # self.running变为false时，跳出循环，停止录音
        stream.close()  # 关闭流
        pa.terminate()  # 结束录音


    #图形界面
    def display(self):
        pygame.mixer.init()  # 初始化pygame的音频模块
        root = Tk()  # 主窗口
        root.resizable(0, 0)  # 尺寸不可修改
        root.title('TalkingBot')  # 标题
        label_prompt = Label(root, text='准备就绪')  # 提示标
        label_prompt.grid(row=2, column=0)  # 在界面指定位置放置提示标
        #txt = Text(root, width=25, height=15, font="Helvetica 20", bg='#EEEBAA', bd=10)  # 聊天记录文本框
        txt = Text(root, width=25, height=15, font="Helvetica 20", bg='#AFEEEE', bd=10)  # 聊天记录文本框

        txt.grid(row=0, column=0)  # 在界面指定位置放置文本框

        def start():
            btn.config(image=stop_img, command=stop)  # 修改按钮图片及功能
            threading._start_new_thread(self.read_audio, ())  # 新线程
            label_prompt.config(text='正在录音...')  # 提示：“正在录音”


        def stop():
            self.running = False  # 按下停止录音按钮，self.running变为false，跳出录音循环
            btn.config(image=start_img, command=start)  # 修改按钮图片及功能 回到初始状态
            label_prompt.config(text='准备就绪')  # 提示：“准备就绪”
            root.update()  # 更新窗口，添加这行代码，解决了按钮图片更新不及时的问题
            self.save_wav('record_test.wav')  # 保存录音至文件
            speech_recognize()  # 进行语音识别

        #百度语音识别
        def speech_recognize():
            def get_file_content(filePath):  # 获取文件内容
                with open(filePath, 'rb') as fp:  # 打开文件
                    return fp.read()  # 读取音频文件内容
            s = self.client.asr(get_file_content('record_test.wav'), 'wav', 8000, {'dev_pid': 1537})  # 进行语音识别，从录音得到的音频文件中识别
            print(s)  # 打印识别返回的字典
            if s['err_msg'] == 'success.':  # 若成功
                str1 = s['result'][0]  # 提取文字部分
                txt.insert(INSERT, '我: '+str1+'\n')  # 在文本框中显示识别结果
                root.update()  # 刷新窗口
                print(str1)  # 控制台输出识别结果文字（可删去）
                robot(str1)  # 把识别出来的文字内容交给机器人处理
            else:
                label_prompt.config(text='录音失败，请重试')  # 录音质量不佳、网络问题，会导致识别失败，若失败，进行提示

        #播放合成的语音
        def play_audio(filename):
            flag = False
            pygame.mixer.init()  # 初始化pygame音频模块
            while True:
                if flag == False:  # 若尚未播放
                    pygame.mixer.music.load(filename)  # 加载
                    pygame.mixer.music.play()  # 播放
                if pygame.mixer.music.get_busy() == True:  # 若已播放完毕
                    flag = True
                else:
                    if flag:
                        pygame.mixer.music.stop()  # 停止播放
                        break

        #机器人处理             
        def robot(text_input):
            api_url = "http://openapi.tuling123.com/openapi/api/v2"  # url地址
            req = {
                "perception":
                {
                    "inputText":
                    {
                        "text": text_input  # 交给机器人的文字信息（上一步语音识别获得）
                    },

                    "selfInfo":  # 用户信息，以进行对机器人的个性化定制
                    {
                        "location":
                        {
                            "city": "******",
                            "province": "*****",
                            "street": "*****"  # 地点信息，播报天气
                        }
                    }
                },

                "userInfo": 
                {
                    "apiKey": "*************",
                    "userId": "********"  # 图灵机器人开发者注册信息（尚未实名认证）
                }
            }
            req = json.dumps(req).encode('utf8')# 将字典格式的req编码为utf8
            http_post = urllib.request.Request(api_url, data=req, headers={'content-type': 'application/json'})
            response = urllib.request.urlopen(http_post)
            response_str = response.read().decode('utf8')
            response_dic = json.loads(response_str)
            intent_code = response_dic['intent']['code']
            results_text = response_dic['results'][0]['values']['text']  # 得到返回的文字

            print('答:'+results_text)  # 控制台输出机器人回答内容
            txt.insert(INSERT, 'Bot: '+results_text+'\n\n')  # 在文本框显示机器人的回答
            root.update()  # 刷新窗口
            output1 = self.client.synthesis(results_text, 'zh', 1, {'vol':5, 'per':4, 'spd':2})  # 对机器人返回的文字，进行语音合成
            print('synthesis called')  # 控制台提示“语音合成已调用”
            # 识别正确返回语音二进制 错误则返回dict
            if not isinstance(output1, dict):  # 若成功
                with open('output.mp3','wb') as f:  # 打开音频文件
                    f.write(output1)  # 写入音频文件
            play_audio('output.mp3')  # 播放合成的语音文件


        start_img = PhotoImage(file='mic3.png')  # 按钮贴图
        stop_img = PhotoImage(file='mic3_stop2.png')  # 按钮贴图
        btn = Button(root, command=start, width=100, height=100, image=start_img)  # 录音/停止按钮
        btn.grid(row=1, column=0)  # 在界面指定位置放置按钮
        mainloop()  # tkinter mainloop
        
        
#主函数
if __name__ == "__main__":
    r = Recorder()  # 建立上述Recorder类的一个实例
    r.display()  # 显示界面，开始运行程序
    