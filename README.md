# PDFConcierge

읽을거리 서비스를 제공하는 사이트에서 새 글을 받아 지정된 공간에 업로드 합니다.

## 지원하는 사이트
각 서비스의 계정 인증이 필요한 경우가 있습니다.
* [매경 다이제스트](http://digest.mk.co.kr)
  * PDF (원본, ~~A4, Kindle~~)
  * 오디오북 (ID3 태그 수정 및 책 표지 앨범아트 적용)
* [朝日新聞](https://www.asahi.com)
  * 社説 (US Letter PDF, 当日朝刊のみ)
* [読売新聞](https://www.yomiuri.co.jp)
  * 社説 (US Letter PDF, 当日朝刊のみ)
* [The New Yorker](https://www.newyorker.com)
  * Daily Comment (US Letter PDF)

## 지원하는 클라우드 서비스
* [Dropbox](https://dropbox.com)

## 사용법
### Docker
#### Build
<code>docker build -t noxowl/pdf-concierge:latest .</code>
#### Fetch from the 매경 다이제스트
<code>
docker run --rm -it --name pdf-concierge -e PDFC_CLOUD_TOKEN={YOUR TOKEN} -e PDFC_MK_ID={YOUR MK ID} -e PDFC_MK_PW={YOUR MK PW} noxowl/pdf-concierge:latest
</code>

#### Fetch from the Press
<code>
docker run --rm -it --name pdf-concierge -e PDFC_CLOUD_TOKEN={YOUR TOKEN} -e PDFC_ASAHI=true -e PDFC_YOMIURI=true -e PDFC_NEW_YORKER=true noxowl/pdf-concierge:latest
</code>

### 로컬에서 실행
차후 갱신

## 책임한계
이 프로그램은 개인 사용을 전제로 하며, [MIT 라이선스](https://olis.or.kr/license/Detailselect.do?lId=1006) 하에 배포됩니다. 기업 및 단체의 이용은 금지되지 않으나, 본 프로그램 작성자는 프로그램 이용에 대한 책임을 지거나 사용상 발생하는 문제에 관한 그 어떠한 지원도 할 수 없음을 명시합니다.

본 프로그램을 통해 파일을 저장하는 행위는 사적 이용을 위한 복제에 해당하며, 저장된 파일을 이용 권한이 없는 불특정 다수의 사람들과 공유하는 경우 저작권법에 의해 처벌될 수 있음을 양지하여 주시기 바랍니다.