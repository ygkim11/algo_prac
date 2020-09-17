import os
import sys

from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode_prac import *
from PyQt5.QtTest import *
from config.kiwoomType_prac import *

class Kiwoom(QAxWidget):
    def __init__(self):

        ###뭔지 알아내기????#####
        super().__init__()
        ########################

        print("kiwoom 클래스 입니다.")

        self.realType = RealType()

        ####EVENTLOOP 모음######
        self.login_event_loop = None
        self.detail_account_info_event_loop = QEventLoop()
        self.calculator_event_loop = QEventLoop()
        #######################

        #########스크린번호 모음
        self.screen_my_info = "2000"
        self.screen_calculation_stock = "4000"
        self.screen_real_stock = "5000"
        self.screen_meme_stock = "6000"
        self.screen_start_stop_real = "1000"

        #####변수 모음
        self.account_num = None
        self.account_stock_dict = {}
        self.not_account_stock_dict = {}

        self.portfolio_stock_dict = {}
        self.jango_dict = {}

        ############################

        ######계좌관련 변수
        self.use_money = 0
        self.use_money_percent = 0.01
        ###############################

        ##### 종목 분석용 #############
        # self.calcul_data = []
        ##############################

        self.get_ocx_instance()
        self.event_slots()
        self.real_events_slots()

        #####아래 함수 세팅에 대한 최종 실행 공간#######
        self.signal_login_commConnect()
        self.get_account_info()
        self.detail_account_info() #예수금 가져오기!!
        self.detail_account_mystock() #계좌잔고 가져오기
        self.not_concluded_account() #미체결
        # self.calculator_fnc() #종목 분석용, 임시용으로 실행
        ##############################################

        self.read_code() #저장된 종목들 불러오기

        self.screen_number_setting()

        self.dynamicCall("SetRealReg(QString,QString,QString,QString)", self.screen_start_stop_real, "", self.realType.REALTYPE['장시작시간']['장운영구분'], "0") #처음등록할땐 0 이후에 추가는 1!

        for code in self.portfolio_stock_dict.keys():
            screen_num = self.portfolio_stock_dict[code]['스크린번호']
            fids = self.realType.REALTYPE['주식체결']['체결시간']
            #실시간 등록은 SetRealReg
            self.dynamicCall("SetRealReg(QString,QString,QString,QString)", screen_num, code, fids, "1")  # 처음등록할땐 0 이후에 추가는 1!
            print("실시간 등록 코드: %s, 스크린번호: %s, fid번호: %s" % (code, screen_num, fids))

    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def real_events_slots(self):
        self.OnReceiveRealData.connect(self.realdata_slot)
        self.OnReceiveChejanData.connect(self.chejan_slot)

    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")

        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def login_slot(self,errCode):
        print(errors(errCode))

        self.login_event_loop.exit()

    def get_account_info(self):
        account_list =self.dynamicCall("GetLogininfo(QString)", "ACCNO")

        self.account_num = account_list.split(';')[0]  #실계좌 투자시 1 로 바꿔주자(내 계좌가 두번째에 있음)

        print("나의 보유 계좌번호 %s" % self.account_num ) #8131920111

    def detail_account_info(self):
        print("예수금 요청 정보 작성")

        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, Int, String)", "예수금상세현황요청", "opw00001", "0", self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def detail_account_mystock(self, sPrevNext="0"):
        print("계좌평가 잔고내역 요청 연속시 2 <= %s" % sPrevNext)

        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, Int, String)", "계좌평가잔고내역요청", "opw00018", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()


    def not_concluded_account(self, sPrevNext="0"):
        print("미체결요청")

        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("CommRqData(QString, QString, Int, QString)", "실시간미체결요청", "opt10075", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()





    ################## TR 요청 ######################


    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        '''
        TR요청 받는 함수
        :param sScrNo: 스크린번호
        :param sRQName: 요청 이름(내가 지정)
        :param sTrCode: 요청ID, TR코드
        :param sRecordName: 사용안함
        :param sPrevNext: 다음페이지가 있는지
        :return:
        '''

        if sRQName == "예수금상세현황요청":
            deposit = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "예수금")
            print("예수금 : %s" % int(deposit))

            ###예수금에서 얼마 비중씩 살지
            self.use_money = int(deposit) * self.use_money_percent
            self.use_money = self.use_money / 4

            avail_deposit = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "출금가능금액")
            print("출금가능금액 : %s" % int(avail_deposit))

            self.detail_account_info_event_loop.exit()

        ###################################

        elif sRQName == "계좌평가잔고내역요청":
            total_buy_amount = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "총매입금액")
            total_buy_amount_result = int(total_buy_amount)

            print("총매입금액 : %s" % total_buy_amount_result)

            total_return = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "총수익률(%)")
            total_return_result = float(total_return)

            print("총수익률(%%) : %s" % total_return_result) # %가 문자열 반환에 활용돼 %% 로 작성해야 총수익률(%)로 인식함!




            rows = self.dynamicCall("GetRepeatCnt(Qstring, Qstring)", sTrCode, sRQName)

            cnt = 0
            for i in range(rows):
                code = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "종목번호")
                code = code.strip()[1:]

                code_nm = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "종목명")
                stock_quantity = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "보유수량")
                buy_price = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "매입가")
                learn_rate = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "수익률(%)")
                current_price = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "현재가")
                total_chegual_price = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "매입금액")
                possible_quantity = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "매매가능수량")

                if code in self.account_stock_dict:
                    pass
                else:
                    self.account_stock_dict.update({code:{}})


                code_nm = code_nm.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())
                current_price = int(current_price.strip())
                total_chegual_price = int(total_chegual_price.strip())
                possible_quantity = int(possible_quantity.strip())

                self.account_stock_dict[code].update({"종목명": code_nm})
                self.account_stock_dict[code].update({"보유수량": stock_quantity})
                self.account_stock_dict[code].update({"매입가": buy_price})
                self.account_stock_dict[code].update({"수익률(%)": learn_rate})
                self.account_stock_dict[code].update({"현재가": current_price})
                self.account_stock_dict[code].update({"매입금액": total_chegual_price})
                self.account_stock_dict[code].update({"매매가능수량": possible_quantity})

                ### ex) {"02039" : {"종목명":"xx","보유수량": 10......} ##########

                cnt += 1


            print("계좌에 가지고 있는 종목 : %s" % self.account_stock_dict)
            print("계좌보유종목 카운트 %s" % cnt)

            if sPrevNext == "2":
                self.detail_account_mystock(sPrevNext="2")
            else:
                self.detail_account_info_event_loop.exit()

        ####################################

        elif sRQName == "실시간미체결요청":

            ####미체결 종목이 없으면 아래에서 카운트가 안되고 그냥 끝남

            rows = self.dynamicCall("GetRepeatCnt(Qstring, Qstring)", sTrCode, sRQName)

            for i in range(rows):

                code = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "종목코드")
                code_nm = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "종목명")
                order_no = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "주문상태") #접수/확인/체결
                order_quantity = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "주문수량")
                order_price = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "주문가격")
                order_gubun = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "주문구분") #-매도,+매수,
                not_quantity = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "미체결수량")
                ok_quantity = self.dynamicCall("GetCommData(Qstring, Qstring, int, Qstring)", sTrCode, sRQName, i, "체결량")

                code = code.strip()
                code_nm = code_nm.strip()
                order_no = int(order_no.strip())
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                order_gubun = order_gubun.strip().lstrip("+").lstrip("-")
                not_quantity = int(not_quantity.strip())
                ok_quantity = int(ok_quantity.strip())

                if order_no in self.not_account_stock_dict:
                    pass
                else:
                    self.not_account_stock_dict[order_no] = {}

                nasd = self.not_account_stock_dict[order_no]

                nasd.update({"종목코드" : code})
                nasd.update({"종목명" : code_nm})
                nasd.update({"주문번호" : order_no})
                nasd.update({"주문상태" : order_status})
                nasd.update({"주문수량" : order_quantity})
                nasd.update({"주문가격" : order_price})
                nasd.update({"주문구분" : order_gubun})
                nasd.update({"미체결수량" : not_quantity})
                nasd.update({"체결량": ok_quantity})

                print("미체결 종목 : %s" % self.not_account_stock_dict[order_no])


            #######....이 한줄이 For 문 안에 들어있어서 Eventloop가 종료가 안됐었다...ㅎㅎㅎㅎㅎㅎ##############
            self.detail_account_info_event_loop.exit()



    ################## TR 요청 END ######################



    def get_code_list_by_market(self, market_code):
        '''
        종목코드 반환  (개발가이드 > 기타함수> 종목정보관련함수)
        :param market_code:
        :return:
        '''
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_code)
        code_list = code_list.split(";")[:-1]

        return code_list


    def read_code(self):
        if os.path.exists("files/stock_pick.txt"):
            f = open("files/stock_pick.txt", "r", encoding="utf-8-sig")

            lines = f.readlines()
            for line in lines:
                if line != "":
                    ls = line.split("\t") #["005843" , "종목명", "현재가\n"]

                    # print(ls)

                    stock_code = ls[0]
                    stock_name = ls[1]
                    stock_price = int(ls[2].split("\n")[0])
                    stock_price = abs(stock_price)  #종목이 하락시 -9000 이런식으로 데이터 나옴..! abs 필요

                    self.portfolio_stock_dict.update({stock_code:{"종목명":stock_name, "현재가":stock_price}})

                f.close()

                print(self.portfolio_stock_dict)


    def screen_number_setting(self):

        screen_overwrite = []

        #계좌평가잔고내역 종목 갖고오기
        for code in self.account_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        #미체결에 있는 종목들
        for order_number in self.not_account_stock_dict.keys():
            code = self.not_account_stock_dict[order_number]["종목코드"]
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        #포트폴리오에 담겨있는 종목들
        for code in self.portfolio_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        #스크린번호 할당
        cnt = 0
        for code in screen_overwrite:

            temp_screen = int(self.screen_real_stock)
            meme_screen = int(self.screen_meme_stock)

            #한 스크린번호당 50개 종목씩만 넣기 위해, 최대 100개까지 넣을 수 있음!
            if (cnt % 50) == 0:
                temp_screen += 1 #스크린번호 5001이 됨
                self.screen_real_stock = str(temp_screen)

            if (cnt % 50) == 0:
                meme_screen += 1
                self.screen_meme_stock = str(meme_screen)

            if code in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict[code].update({"스크린번호": str(self.screen_real_stock)})
                self.portfolio_stock_dict[code].update({"주문용스크린번호": str(self.screen_meme_stock)})

            elif code not in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict.update({code: {"스크린번호": str(self.screen_real_stock), "주문용스크린번호": str(self.screen_meme_stock)}})

            cnt += 1

        #현재가가 같이 업데이트는 안되네?
        print(self.portfolio_stock_dict)


    #######Realdata SLOT ###############################################
    def realdata_slot(self, sCode, sRealType, sRealData):

        if sRealType == "장시작시간":
            fid  = self.realType.REALTYPE[sRealType]['장운영구분']
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)

            if value == "0":
                print("장 시작 전")
            elif value == "3":
                print("장 시작!")
            elif value == "2":
                print("장 종료, 동시호가")
            elif value == "4":
                print("3시 30분 장 종료!")

                for code in self.portfolio_stock_dict.keys():
                    self.dynamicCall("SetRealRemove(QString, QString)", self.portfolio_stock_dict[code]["스크린번호"], code)

                QTest.qWait(5000)

                #장끝난후 Stock_Pick 파일 지우고 / Calculation 시작하는 부분~!
                self.file_delete()
                # self.calculator_fnc()

                sys.exit()

        elif sRealType == "주식체결":
            a = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]["체결시간"]) #hhmmss string 형태

            b = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]["현재가"])  # +(-) 2500 string 형태
            b =abs(int(b))

            c = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]["전일대비"]) # -(+)
            c = abs(int(c))

            d = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]["등락율"])  # -(+)
            d = float(d)

            e = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]["(최우선)매도호가"])  # -(+)
            e = abs(int(e))

            f = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]["(최우선)매수호가"])  # -(+)
            f = abs(int(f))

            g = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]["거래량"])  # -(+) 틱봉의 아주작은 거래량들!
            g = abs(int(g))

            h = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]["누적거래량"])  # -(+)
            h = abs(int(h))

            i = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]["고가"])  # -(+)
            i = abs(int(i))

            j = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]["시가"])  # -(+)
            j = abs(int(j))

            k = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]["저가"])  # -(+)
            k = abs(int(k))

            if sCode not in self.portfolio_stock_dict:
                self.portfolio_stock_dict.update({sCode:{}})

            self.portfolio_stock_dict[sCode].update({"체결시간" : a})
            self.portfolio_stock_dict[sCode].update({"현재가": b})
            self.portfolio_stock_dict[sCode].update({"전일대비": c})
            self.portfolio_stock_dict[sCode].update({"등락율": d})
            self.portfolio_stock_dict[sCode].update({"(최우선)매도호가": e})
            self.portfolio_stock_dict[sCode].update({"(최우선)매수호가": f})
            self.portfolio_stock_dict[sCode].update({"거래량": g})
            self.portfolio_stock_dict[sCode].update({"누적거래량": h})
            self.portfolio_stock_dict[sCode].update({"고가": i})
            self.portfolio_stock_dict[sCode].update({"시가": j})
            self.portfolio_stock_dict[sCode].update({"저가": k})

            # print(self.portfolio_stock_dict[sCode])

            ##############실시간 조건문 구성 시작 (61) #####################

            #이전 계좌잔고평가내역에 있고 오늘 산 잔고에는 없을 경우
            if sCode in self.account_stock_dict.keys() and sCode not in self.jango_dict.keys():
                print("%s %s" % ("신규매도를 한다", sCode))

                asd = self.account_stock_dict[sCode]

                meme_rate = (b -asd['매입가']) / asd['매입가'] * 100

                if asd['매매가능수량'] > 0 and (meme_rate > 5 or meme_rate < -5):

                #nOrderTpe: 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정 / 우리는 2:신규매도 사용
                # 시장가주문으로 세팅! config KiwoomType.py도 사용됨!
                # 원주문번호는 비어있지만, 매수정정이 들어가면 원주문번호 채워줘야함

                    order_sucess = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                                    ["신규매도", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 2,
                                                    sCode, asd['매매가능수량'], 0 , self.realType.SENDTYPE["거래구분"]["시장가"], ""])
                    #dynamicCall 에 들어가는 변수가 너무많으면 list로 감싸줘서 해결하면 된다!

                    if order_sucess == 0:
                        print("매도주문 전달 성공")
                        #실제로는 좀더 자세히 확인필요/ 주문잘들어갓고, 수량 어떻고 다 체크후 지우는게 맞음 차후에 확장필요
                        del self.account_stock_dict[sCode]
                    else:
                        #errorCode.py 부분이랑 연결해서 봐야댐 / 코딩 추가하기!
                        print("매도주문 전달 실패")



            #오늘 산 잔고에 있을 경우
            elif sCode in self.jango_dict.keys():
                print("%s %s" % ("신규매도를 한다2", sCode))
                jd = self.jango_dict[sCode]
                meme_rate = (b-jd['매입단가']) / jd['매입단가'] * 100

                if jd['주문가능수량'] > 0 and (meme_rate > 5 or meme_rate < -5):

                    order_sucess = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                                    ["신규매도", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 2,
                                                     sCode, jd['주문가능수량'], 0, self.realType.SENDTYPE["거래구분"]["시장가"], ""])

                    #jango dict는 아래에서 끝까지 확인하고 이미 Del 함! 위에처럼 여기서 del 안해줘도 된다.
                    #logging.logger.debug????
                    if order_sucess == 0:
                        print("매도주문 성공!")
                        # self.logging.logger.debug("매도주문 전달 성공")
                    else:
                        print("매도주문 실패!")
                        # self.logging.logger.debug("매도주문 전달 실패")


            #등락율이 2.0% 이상이고 오늘 산 잔고에 없을 경우
            elif d>2.0 and sCode not in self.jango_dict:
                print("%s %s" % ("신규매수를 한다", sCode))

                result = (self.use_money*0.1) / e #내가 가진돈 의 10% / 최우선 매도호가의 몫 만큼 사겟다!
                quantity = int(result)

                #최우선 매도호가에 지정가 거래
                order_sucess = self.dynamicCall(
                    "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                    ["신규매수", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 1,
                     sCode, quantity, e, self.realType.SENDTYPE["거래구분"]["지정가"], ""]
                )
                if order_sucess == 0:
                    print("매수주문 성공!")
                    # self.logging.logger.debug("매수주문 전달 성공")
                else:
                    print("매수주문 실패!")
                    # self.logging.logger.debug("매수주문 전달 실패")



            not_meme_list = list(self.not_account_stock_dict) #list함수를 씌우면 주소가 바뀌어서 결과 list가 변해도 기존의 dict는 변하지않는다!
            #만드는 이유: 여기서 계산하고 있는 도중에 갑자기 신규 매매가 들어오면 오류 생성되기 때문에!
            #아래루프 돌릴때 for order_num in self.not_account_stock_dict: 이런식으로 코딩하면 계산수행중 신규 매매시 루프의 횟수가 갑자기 늘어남!
            for order_num in not_meme_list:
                code = self.not_account_stock_dict[order_num]["종목코드"]
                meme_price = self.not_account_stock_dict[order_num]["주문가격"]
                not_quantity = self.not_account_stock_dict[order_num]["미체결수량"]
                # meme_gubun = self.not_account_stock_dict[order_num]["매도수구분"] #"매수" or "매도"가 str 형태로 출력 ...근데 미체결내역에 코딩이 안돼있는거 같은데?;;
                order_gubun = self.not_account_stock_dict[order_num]["주문구분"]

                if order_gubun == "매수" and not_quantity > 0 and e >meme_price:
                    print("%s %s" % ("매수취소", sCode))

                    # 0이면 전량 취소!
                    order_sucess = self.dynamicCall(
                        "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                        ["매수취소", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 3,
                         code, 0, 0, self.realType.SENDTYPE["거래구분"]["지정가"], order_num]
                    )

                    if order_sucess == 0:
                        print("매수취소 성공!")
                        # self.logging.logger.debug("매수취소 전달 성공")
                    else:
                        print("매수취소 실패!")
                        # self.logging.logger.debug("매수취소 전달 실패")


                elif not_quantity == 0:
                    del self.not_account_stock_dict[order_num] #단타칠게 아니면 없어도됨; 미체결 취소하면 어차피 사라지기 때문에 dict도 지워서 초기화 (61) 16:00

            #주문시작! -> 접수 -> 확인 -> 체결 -> 잔고내역으로 -> 체결(남은 미체결수량) -> 잔고내역으로!(매수하든 매도하든)


    def chejan_slot(self, sGubun, nItemCnt, sFIdList): #주문에 대한 내역은 다 여기서 받는다!

        if int(sGubun) == "0": #체결내역 알려줌 4989화면(미체결)
            print("주문체결")
            account_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["계좌번호"])
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["종목코드"])[1:] #"A00707" A 제거위해서
            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["종목명"])
            stock_name = stock_name.strip()

            origin_order_number = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["원주문번호"]) #처음은 원주문번호 Default값 "000000"
            order_number = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["주문번호"])

            order_status = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["주문상태"]) #출력: 접수, 확인, 체결

            order_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["주문수량"]) #출력 : "3"
            order_quan = int(order_quan)

            order_price =self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["주문가격"]) #출력 : "3200"
            order_price = int(order_price)

            not_chegual_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["미체결수량"]) #출력: 22, Default: 0
            not_chegual_quan = int(not_chegual_quan)

            order_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["주문구분"])
            order_gubun = order_gubun.strip().lstrip("+").lstrip("-")

            # meme_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["매도수구분"]) #매수: 2, 매도: 1
            # #KiwoomType.py에서 2 -> 매수/ 1 -> 매도로 바꿔줌
            # meme_gubun = self.realType.REALTYPE["매도수구분"][meme_gubun]

            chegual_time_str = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["주문/체결시간"]) #출력: 151028 hhmmss

            chegual_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["체결가"]) #출력: 2110 default: ""

            if chegual_price == "":
                chegual_price = 0
            else:
                chegual_price = int(chegual_price)

            chegual_quantity = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["체결량"]) #출력: 22 default: ""

            if chegual_quantity == "":
                chegual_quantity = 0
            else:
                chegual_quantity = int(chegual_quantity)

            current_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["현재가"])
            current_price = int(current_price)

            first_sell_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["(최우선)매도호가"])
            first_sell_price = abs(int(first_sell_price))

            first_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE["주문체결"]["(최우선)매수호가"])
            first_buy_price = abs(int(first_buy_price))

            ######## 새로 들어온 주문이면 주문번호 할당
            if order_number not in self.not_account_stock_dict.keys():
                self.not_account_stock_dict.update({order_number: {}})

            self.not_account_stock_dict[order_number].update({"종목코드": sCode})
            self.not_account_stock_dict[order_number].update({"주문번호": order_number})
            self.not_account_stock_dict[order_number].update({"종목명": stock_name})
            self.not_account_stock_dict[order_number].update({"주문상태": order_status})
            self.not_account_stock_dict[order_number].update({"주문수량": order_quan})
            self.not_account_stock_dict[order_number].update({"주문가격": order_price})
            self.not_account_stock_dict[order_number].update({"미체결수량": not_chegual_quan})
            self.not_account_stock_dict[order_number].update({"원주문번호": origin_order_number})
            self.not_account_stock_dict[order_number].update({"주문구분": order_gubun})
            #삭제 요청
            # self.not_account_stock_dict[order_number].update({"매도수구분": meme_gubun})
            self.not_account_stock_dict[order_number].update({"주문/체결시간": chegual_time_str})
            self.not_account_stock_dict[order_number].update({"체결가": chegual_price})
            self.not_account_stock_dict[order_number].update({"체결량": chegual_quantity})
            self.not_account_stock_dict[order_number].update({"현재가": current_price})
            self.not_account_stock_dict[order_number].update({"(최우선)매도호가": first_sell_price})
            self.not_account_stock_dict[order_number].update({"(최우선)매수호가": first_buy_price})

            print(self.not_account_stock_dict)





        elif int(sGubun) == 1: #잔고내역 알려줌 4989화면(잔고)
            print("잔고")

            account_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['계좌번호'])
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목코드'])[1:]

            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목명'])
            stock_name = stock_name.strip()

            current_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['현재가'])
            current_price = abs(int(current_price))

            stock_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['보유수량'])
            stock_quan = int(stock_quan)

            avail_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['주문가능수량'])
            avail_quan = int(avail_quan)

            buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매입단가']) #종목 평단가
            buy_price = abs(int(buy_price))

            total_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['총매입가']) #포트폴리오 전체 매입금액
            total_buy_price = int(total_buy_price)

            meme_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매도매수구분']) #아까 체결에서 지웟던건데..다시들어오네?
            meme_gubun = self.realType.REALTYPE["매도수구분"][meme_gubun]

            first_sell_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매도호가'])
            first_sell_price = abs(int(first_sell_price))

            first_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매수호가'])
            first_buy_price = abs(int(first_buy_price))

            if sCode not in self.jango_dict.keys():
                self.jango_dict.update({sCode:{}})

            self.jango_dict[sCode].update({"현재가": current_price})
            self.jango_dict[sCode].update({"종목코드": sCode})
            self.jango_dict[sCode].update({"종목명": stock_name})
            self.jango_dict[sCode].update({"보유수량": stock_quan})
            self.jango_dict[sCode].update({"주문가능수량": avail_quan})
            self.jango_dict[sCode].update({"매입단가": buy_price})
            self.jango_dict[sCode].update({"총매입가": total_buy_price})
            self.jango_dict[sCode].update({"매도매수구분": meme_gubun})
            self.jango_dict[sCode].update({"(최우선)매도호가": first_sell_price})
            self.jango_dict[sCode].update({"(최우선)매수호가": first_buy_price})

            print(self.jango_dict)

            if stock_quan == 0:
                del self.jango_dict[sCode]
                self.dynamicCall("SetRealRemove(QString, QString)", self.portfolio_stock_dict[sCode]['스크린번호'], sCode)


    #송수신 메세지 Get
    def msg_slot(self, sScrNo, sRQName, sTrCode, msg):
        print("스크린: %s, 요청이름: %s, tr코드: %s --- %s" %(sScrNo, sRQName, sTrCode, msg))

    #Stock_Pick 파일 삭제용 함수
    def file_delete(self):
        if os.path.isfile("files/stock_pick.txt"):
            os.remove("files/stock_pick.txt")