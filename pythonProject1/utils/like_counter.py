
import asyncio
# import nest_asyncio

# nest_asyncio.apply()

async def like_counter(origin_message_id, message_html_value):

    # global dict_of_questionnaire_evaluation

    message_html : str = message_html_value
    like_value : str = 0
    super_like_value : str = 0

    print('message_html_value-', message_html_value)

    if message_html.find('Отдай симпатию ❣') != -1:
      print('Нашли по индексу = ',message_html.find('Отдай симпатию ❣'))

      print("message_html[message_html.find('Отдай супер симпатию ❤')+19",
      message_html[message_html.find('Отдай супер симпатию ❤')+22:message_html.find('¹²⁹⁰⁹⁸⁷')])

      like_value : int = int(message_html[message_html.find('Отдай симпатию ❣')+16:
                                      message_html.find('⁸¹²⁰⁹⁷⁹')
                                      ])
      print('like_value =', like_value)
      print('Нашли по индексу = ',message_html.find('Отдай супер симпатию ❤'))
      super_like_value : int = int(message_html[message_html.find('Отдай супер симпатию ❤')+22:
                                      message_html.find('¹²⁹⁰⁹⁸⁷')
                                      ])
      print('super_like_value =', super_like_value)


    #like_value = 51
    #super_like_value = 3

    # dict_of_questionnaire_evaluation[origin_message_id]["like"] = like_value
    # dict_of_questionnaire_evaluation[origin_message_id]["super_like"] = super_like_value

    return like_value, super_like_value

message_html_value = '. (https://ift.tt/K0Nq8aX)'
message_html_value += '\nSukaDaddу'



#https://ift.tt/AX1akD3
#ТГ @LookingForSW
##не_см_flog_ru #ж_верх #знакомства #низ

#1. SukaDaddy
#2. Мужской, 36
#3. Москва, ЦАО #Москва
#Раскрыть ⬇⬇⬇

#4. Низ
#5. Верхнюю женщину или девушку-свитча (доминирует надо мною, но сама может подчиняться другим мужчинам). Возраст 18-25 или 45+ лет желателен, но не критично.
#6. Интересы:
#А) БДСМ — практики: куколд, фф, плевки, пощечины, моральные унижения, пажизм, пресмыкания, чувство принадлежности, фетиш нейлона, тату, пирсинга и обуви. При длительных отношениях возможны феминизация, финдом, зд, пояс верности. Остальные интересы — желания Хозяйки в рамках моих табу.
#Б) Сексуальные практики: куколд, мЖМ, мЖММ, мжМ, мжММ, куни, ани, оральный секс, ageplay, cosplay.
#7. Табу: ПУБЛИЧНОСТЬ. Фото и видеообмен. Камеры. Скайп. Обмен обнаженными фото. Съемка меня. Копро, увечья, кровь, месячные, клеймление, ожоги, порезы, гигантские страпоны, анальный секс в мою сторону, секс с Хозяйкой(за исключением куколд-практик), сперма, кастрация, кредитный фемдом, ЛС на чужой территории.
#8. Как связаться? @LookingForSW
#9. Расскажу о себе: я в жизни лидер, руководящая должность в IT-сфере, несколько высших образований, а в отношениях подкаблучник.
#Очень отзывчив и гибок к хотелкам МОЕЙ дамы.
#По крайней мере в последних трех долгих отношениях длительностью 7, 5 и 3 года так было.
#Решаю ее проблемы(в меру возможностей), удовлетворяю капризы(в рамках ресурсов), закрываю глаза на косяки(напр.флирт, измены). Такое раздвоение личности объяснимо:
#компенсирую эту «слабость» с женщиной силой на руководящей работе и в социальной жизни. Ищу внешне нормальные отношения где мужчина содержит даму, ограждает ее от реалий внешнего мира, подчиняется ей и не ревнует.
#СТАТУС:
#_________________
#Интегральная оценка(22.5)
message_html_value += '\nОтдай лайк 💟538844'
message_html_value += '\n⁸¹²⁰⁹⁷⁹'

message_html_value += '\nОтдай суперлайк 🔥38090'
message_html_value += '\n¹²⁹⁰⁹⁸⁷'
#asyncio.run(like_counter(1,message_html_value))
