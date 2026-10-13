# Анализ курса: Технологии обработки больших данных 2026

Источник: `/Users/pavelnehaenko/Desktop/ChatExport_2026-06-23`

Дата анализа: 2026-06-23

## Что найдено

- Сообщений в Telegram-экспорте: 205.
- PDF-файлов: 17.
- Экзамен: 27 июня 2026 в 12:00, по сообщению от 2026-06-22.
- Автомат: все лабораторные должны быть сданы в дедлайн, по сообщению от 2026-06-11.
- Примечание по PDF-ссылкам: длинные URL в PDF могут быть физически перенесены на следующую строку, поэтому часть таких ссылок ниже может требовать ручного склеивания с контекстом исходного PDF.

## Практическая часть

- ЛР1: Классический жизненный цикл ML-модели. GitHub, данные, ML-модель, API, тесты, DVC, Docker, конфиги, CI/CD, DockerHub, отчет, zip.
- ЛР2: Взаимодействие с источниками данных. Форк ЛР1, БД по варианту, секреты не в коде, docker-compose, CI/CD, отчет, GitHub, DockerHub, zip.
- ЛР3: Секреты в хранилище. Hashicorp Vault или Ansible Vault, DB-секреты в хранилище, получение секретов сервисом, docker-compose, CI/CD.
- ЛР4: Apache Kafka. Producer, consumer, передача результата модели, интеграция Kafka с secret storage и БД, docker-compose, CI/CD.
- ЛР5: PySpark clustering. Spark, WordCount, k-means на OpenFoodFacts, предобработка под ресурсы, отчет, GitHub, zip.
- ЛР6: Источники данных на PySpark. Выгрузка данных на старте, загрузка результатов после модели, протокол модель-источник, формат хранения, Docker желательно.
- ЛР7: Витрина данных на Spark/Scala. Data mart на Scala, единый протокол/формат, предобработка в витрине, интеграция модель-витрина-источник.
- ЛР8: Миграция на Kubernetes. Spark on Kubernetes, запуск модели/источника/витрины, обновления, оптимизация ресурсов, Helm/OpenShift/k8s secrets допускаются.

## Рекомендуемый порядок подготовки

1. Проверить практику: по каждой ЛР должны быть отчет, GitHub, zip-дистрибутив; для ЛР1-4 также DockerHub/CI/CD где требуется.
2. Готовить теорию блоками: Big Data/Grid/HDFS; БД/CAP/ACID/SQL-NoSQL; ClickHouse/Greenplum; MapReduce/Spark core; Spark runtime/cache/PySpark/JVM; ML project/DVC/Docker/Jenkins/secrets; Kafka; Kubernetes.
3. На каждый вопрос подготовить ответ на 5-7 предложений, пример сценария использования, 2-3 плюса и 2-3 минуса.
4. При нехватке времени приоритет: Spark, Kafka, Kubernetes, HDFS/БД, ML project tooling.

## Экзаменационные вопросы

```text
ВОПРОСЫ ДЛЯ ПОДГОТОВКИ К ЭКЗАМЕНУ ПО УЧЕБНОЙ ДИСЦИПЛИНЕ
   "ТЕХНОЛОГИИ ОБРАБОТКИ БОЛЬШИХ ДАННЫХ" (2025/26 уч. год)
 1. Определение больших данных. 3 “V” of big data. Характеристики больших данных.
 2. Grid технология. Определение. Архитектура.
 3. Примеры задач больших с описанием анализа.
 4. Модели хранения данных. Теорема CAP. ACID свойства.
 5. Распределённая файловая система. HDFS. Архитектура. Особенности, сценарии
    использования. Достоинства и недостатки.
 6. Системы хранения данных NoSQL. ClickHouse. Архитектура. Особенности,
    сценарии использования. Достоинства и недостатки.
 7. SQL и NoSQL. Определения. Сравнения. Сценарии использования.
 8. Гетерогенные СУБД. Greenplum. Архитектура. Особенности, сценарии
    использования. Достоинства и недостатки.
 9. Типы обработки данных. Grid, WMS, All-Pairs абстракции,
 10. Концепция MapReduce вычислений.
 11. Apache Spark: определение, назначение.
 12. Apache Spark: особенности.
 13. Apache Spark: архитектура.
 14. Различия между MapReduce и Spark.
 15. Apache Spark: RDD.
 16. Apache Spark: трансформация и действие (примеры), lineage.
 17. Apache Spark: ленивые вычисления, их плюсы и минусы.
 18. Ленивые вычисления: кэширование.
 19. Конфигурация Spark приложения.
 20. Процесс выполнения Spark приложения.
 21. Использование RDD и кэша во время выполнения Spark приложения.
 22. Взаимодействие Apache Spark с JVM и интерпретатором Python.
 23. Spark History Server: организация мониторинга Spark приложений.
 24. Назначение MLlib, Streaming, SQL, GraphX.
 25. Структура ML проекта. Conda. DVC. Docker. Jenkins. DevOps практики.
    Хранилища секретов.
 26. Apache Kafka. Определение. Топики и партиции. Смещение и чтение данных.
 27. Apache Kafka. Физическая организация партиций. Автоматическое распределение
    сообщений. Хеширование ключей сообщений. Репликация данных.
 28. Apache Kafka. Гарантии доставки сообщений. Дублирование сообщений.
 29. Apache Kafka. Consumer Groups. Kafka Stream, ksql, Spark Streaming.
 30. ETL/ELT процессы. Хранилища, витрины, озёра данных.
 31. Kubernetes. Контейнерная виртуализация. Архитектура. Под.
 32. Kubernetes. Пространства имён. Метки. Переменные среды.
 33. Kubernetes. ConfigMap. Resources. QoS. Монтирование Docker volume.
 34. Kubernetes. HostPath. PersistentVolume, PersistentVolumeClaim.
 35. Kubernetes. Pods communication. Service. Multiple Pods. Headless Service. Pod
    replicas.
 36. Kubernetes. ReplicaSet. Deployment. Recreate. Rolling Update. StatefulSet. StatefulSet:
    headless Service. DaemonSet. Job.
```

## Ссылки из чата

- https://salutejazz.ru/calls/ha4tib?psw=OEsaUksBUEVeWx1EFBVHVlFRAA | 2026-02-06T17:50:50 | Simar | Ссылка на занятие https://salutejazz.ru/calls/ha4tib?psw=OEsaUksBUEVeWx1EFBVHVlFRAA
- https://docs.google.com/spreadsheets/d/1EXSCx0TJIrSXYB0liA1rvnh4edh9w4CfvpvFJcGGtTA/edit?usp=sharing | 2026-02-09T14:58:12 | Simar | Сводка курса https://docs.google.com/spreadsheets/d/1EXSCx0TJIrSXYB0liA1rvnh4edh9w4CfvpvFJcGGtTA/edit?usp=sharing
- https://github.com/IcyAltair/mle-template/tree/main | 2026-02-13T19:09:27 | Simar | Шаблон проекта для 1 работы https://github.com/IcyAltair/mle-template/tree/main
- https://disk.yandex.ru/i/VlLWARxhSEHgOQ | 2026-02-13T19:35:31 | Simar | Запись 2 лекции https://disk.yandex.ru/i/VlLWARxhSEHgOQ
- https://disk.yandex.ru/d/x6zXM0EN05JUMQ | 2026-02-27T19:37:27 | Simar | Запись 3 занятия https://disk.yandex.ru/d/x6zXM0EN05JUMQ
- https://www.cloudbees.com/jenkins/what-is-jenkins | 2026-02-28T19:28:26 | Simar | Здравствуйте, Материал по Jenkins CloudBees https://www.cloudbees.com/jenkins/what-is-jenkins  https://youtube.com/playlist?list=PLg5SS_4L6LYvQbMrSuOjTL1HOiDhUE_5a&si=USZJstL7ew9Vg
- https://youtube.com/playlist?list=PLg5SS_4L6LYvQbMrSuOjTL1HOiDhUE_5a&si=USZJstL7ew9VgAqO | 2026-02-28T19:28:26 | Simar | Здравствуйте, Материал по Jenkins CloudBees https://www.cloudbees.com/jenkins/what-is-jenkins  https://youtube.com/playlist?list=PLg5SS_4L6LYvQbMrSuOjTL1HOiDhUE_5a&si=USZJstL7ew9Vg
- https://youtu.be/I18TNwZ2Nqg?si=KpfYolWj759Uz56V | 2026-02-28T19:28:26 | Simar | Здравствуйте, Материал по Jenkins CloudBees https://www.cloudbees.com/jenkins/what-is-jenkins  https://youtube.com/playlist?list=PLg5SS_4L6LYvQbMrSuOjTL1HOiDhUE_5a&si=USZJstL7ew9Vg
- https://disk.yandex.ru/d/1uZg6Rtf58tU9A | 2026-03-06T19:35:30 | Simar | Запись 4 занятия https://disk.yandex.ru/d/1uZg6Rtf58tU9A
- https://habr.com/ru/articles/1006822/ | 2026-03-06T20:44:19 | Simar | Я устал каждый раз собирать проект с нуля — и сделал универсальный Docker+Python-шаблон / Хабр https://habr.com/ru/articles/1006822/
- https://disk.yandex.ru/d/TH2YQEEGuOus5g | 2026-03-11T18:03:04 | Simar | Запись 5 занятия https://disk.yandex.ru/d/TH2YQEEGuOus5g
- https://disk.yandex.ru/d/wXK3mP3FBPPzMA | 2026-03-18T19:23:56 | Simar | Запись 6 занятия https://disk.yandex.ru/d/wXK3mP3FBPPzMA
- https://disk.yandex.ru/d/nFetQStewOYPzA | 2026-03-20T19:22:19 | Simar | Запись 7 занятия https://disk.yandex.ru/d/nFetQStewOYPzA
- https://disk.yandex.ru/d/RnnibCZjoyqO3Q | 2026-03-27T20:18:14 | Simar | Запись 8 занятия https://disk.yandex.ru/d/RnnibCZjoyqO3Q
- https://loguru.readthedocs.io/ | 2026-04-02T11:36:13 | Simar | 🛠 Loguru: логирование, которое не хочется ненавидеть  Стандартный logging — мощный, но настраивать его — отдельный вид боли. Форматтеры, хендлеры, фильтры, basicConfig… В итоге бол
- https://t.me/+FMH3zPxDuRtiNTFi | 2026-04-02T11:36:13 | Simar | 🛠 Loguru: логирование, которое не хочется ненавидеть  Стандартный logging — мощный, но настраивать его — отдельный вид боли. Форматтеры, хендлеры, фильтры, basicConfig… В итоге бол
- https://disk.yandex.ru/d/e106MVrsj3l3MA | 2026-04-03T20:22:16 | Simar | Запись 9 занятия https://disk.yandex.ru/d/e106MVrsj3l3MA
- https://habr.com/ru/companies/ruvds/articles/1013854/ | 2026-04-09T19:52:44 | Simar | FYI https://habr.com/ru/companies/ruvds/articles/1013854/
- https://disk.yandex.ru/d/yNNLE_a9VuWLBA | 2026-04-15T18:32:24 | Simar | Запись 10 занятия https://disk.yandex.ru/d/yNNLE_a9VuWLBA
- https://disk.yandex.ru/d/Z-hzOSZ-Ez78Tg | 2026-04-24T20:18:48 | Simar | Запись 11 занятия https://disk.yandex.ru/d/Z-hzOSZ-Ez78Tg
- https://disk.yandex.ru/d/L3dMPG5v13TUnw | 2026-04-24T20:19:00 | Simar | Запись 12 занятия https://disk.yandex.ru/d/L3dMPG5v13TUnw
- https://disk.yandex.ru/d/GGA5QW9adcxwSg | 2026-04-29T18:48:33 | Simar | Запись 13 занятия https://disk.yandex.ru/d/GGA5QW9adcxwSg
- https://disk.yandex.ru/d/Jdwn8B9QI0nCgg | 2026-05-08T21:39:43 | Simar | Запись 14 занятия https://disk.yandex.ru/d/Jdwn8B9QI0nCgg
- https://disk.yandex.ru/d/RRc4wIb9lG1Aew | 2026-05-20T18:25:46 | Simar | Запись 15 занятия https://disk.yandex.ru/d/RRc4wIb9lG1Aew
- https://disk.yandex.ru/d/gsPxAl8rnPQlxw | 2026-05-22T19:37:59 | Simar | Запись 16 занятия https://disk.yandex.ru/d/gsPxAl8rnPQlxw
- https://disk.yandex.ru/d/6tWa68JxJDGokA | 2026-05-29T20:25:22 | Simar | Запись 17 занятия https://disk.yandex.ru/d/6tWa68JxJDGokA
- https://disk.yandex.ru/d/Tp_ir-w3lokI8g | 2026-06-05T20:10:31 | Simar | Запись 18 занятия https://disk.yandex.ru/d/Tp_ir-w3lokI8g
- https://disk.yandex.ru/d/kx7bSjvFlJS2HQ | 2026-06-11T20:13:22 | Simar | https://disk.yandex.ru/d/kx7bSjvFlJS2HQ Запись 19 занятия
- https://habr.com/ru/companies/piter/articles/1033096/ | 2026-06-16T08:22:01 | Simar | Сводка курса обновлена. Если присылали работы, но проверки нет, повторите отправку письма с вложениями. Рекомендуемые материалы по Kubernetes: 1) https://habr.com/ru/companies/pite
- https://ftp.zhirov.kz/books/IT/Docker/Kubernetes%20%D0%B2%20%D0%B4%D0%B5%D0%B9%D1%81%D1%82%D0%B2%D0%B8%D0%B8%20%28%D0%9C%D0%B0%D1%80%D0%BA%D0%BE%20%D0%9B%D1%83%D0%BA%D1%88%D0%B0%29.pdf | 2026-06-16T08:22:01 | Simar | Сводка курса обновлена. Если присылали работы, но проверки нет, повторите отправку письма с вложениями. Рекомендуемые материалы по Kubernetes: 1) https://habr.com/ru/companies/pite
- https://www.oreilly.com/library/view/kubernetes-up-and/9781098110192/ | 2026-06-16T08:22:01 | Simar | Сводка курса обновлена. Если присылали работы, но проверки нет, повторите отправку письма с вложениями. Рекомендуемые материалы по Kubernetes: 1) https://habr.com/ru/companies/pite
- https://kubernetes.io/ru/docs/home/ | 2026-06-16T08:22:01 | Simar | Сводка курса обновлена. Если присылали работы, но проверки нет, повторите отправку письма с вложениями. Рекомендуемые материалы по Kubernetes: 1) https://habr.com/ru/companies/pite
- https://k3s.io/ | 2026-06-16T08:22:01 | Simar | Сводка курса обновлена. Если присылали работы, но проверки нет, повторите отправку письма с вложениями. Рекомендуемые материалы по Kubernetes: 1) https://habr.com/ru/companies/pite
- https://github.com/kubernetes-sigs/kubespray | 2026-06-16T08:22:01 | Simar | Сводка курса обновлена. Если присылали работы, но проверки нет, повторите отправку письма с вложениями. Рекомендуемые материалы по Kubernetes: 1) https://habr.com/ru/companies/pite
- https://www.youtube.com/watch?v=2T86xAtR6Fo | 2026-06-16T08:22:01 | Simar | Сводка курса обновлена. Если присылали работы, но проверки нет, повторите отправку письма с вложениями. Рекомендуемые материалы по Kubernetes: 1) https://habr.com/ru/companies/pite
- https://disk.yandex.ru/d/KAq89_R7nkpHkg | 2026-06-18T20:58:48 | Simar | https://disk.yandex.ru/d/KAq89_R7nkpHkg Запись 20 занятия

## Ссылки из PDF

- https://computing.llnl.gov/tutorials/linux_clusters/ | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- http://clusterdesign.org/fat-trees/ | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://filipv.net/2015/08/27/introduction-to-apache-mesos-and-mesosphere-dcos/ | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- http://mesos.apache.org/documentation/latest/architecture/ | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- http://www.allprogrammingtutorials.com/tutorials/introduction-to-apache-zookeeper.php | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://zookeeper.apache.org/doc/r3.1.2/zookeeperOver.html | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- http://cyberx.tistory.com/148 | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://spark.apache.org/ | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://jaceklaskowski.gitbooks.io/mastering-apache-spark/content/spark- | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://cwiki.apache.org/confluence/display/SPARK/PySpark+Internals | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://spark.apache.org/docs/latest/rdd-programming- | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://spark.apache.org/docs/latest/rdd-programming-guide.html#actions | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://jaceklaskowski.gitbooks.io/mastering-apache-spark/spark-DAGScheduler-Stage.html | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- http://multithreaded.stitchfix.com/blog/2015/10/06/spark-for-data-science/ | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://medium.com/@yjhyjhyjh0/spark-rdd-resilient-distributed-datasets- | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://0x0fff.com/spark-memory-management/ | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://www.youtube.com/watch?v=dPHrykZL8Cg | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://spark.apache.org/docs/latest/configuration.html#memory-management | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://www.quora.com/What-are-different-Persistence-levels-in-Apache-Spark | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://jaceklaskowski.gitbooks.io/mastering-apache-spark/content/spark-sparkenv.html | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://spark.apache.org/docs/2.2.0/api/scala/index.html#org.apache.spark.sql.DataFrameReader | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://spark.apache.org/docs/2.2.0/api/scala/index.html#org.apache.spark.sql.DataFrameWriter | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://spark.apache.org/docs/2.2.0/api/scala/index.html#package | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://spark.apache.org/docs/2.2.0/api/python/index.html | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://data-flair.training/blogs/spark-sql-optimization/ | source: 1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4)
- https://t.me/simamur | source: BD_2026_1
- http://www.oracle.com/us/corporate/pricing/exadata-pricelist-070598.pdf | source: BD_2026_1
- https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/ | source: Introduction-to-Kubernetes-RU (2)
- https://azuremarketplace.microsoft.com/ru-ru/marketplace/apps/cloud-infrastructure-services.docker-compose-2016 | source: Introduction-to-Kubernetes-RU (2)
- https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ | source: Introduction-to-Kubernetes-RU (2)
- https://m.yisu.com/zixun/25838.html | source: Introduction-to-Kubernetes-RU (2)
- http://172.17.0.15:8080/ | source: Introduction-to-Kubernetes-RU (2)
- http://my-service:80/ | source: Introduction-to-Kubernetes-RU (2)
- https://kubernetes.io/docs/concepts/services-networking/service/ | source: Introduction-to-Kubernetes-RU (2)
- http://my-service:8080/ | source: Introduction-to-Kubernetes-RU (2)
- http://headless-service:80/ | source: Introduction-to-Kubernetes-RU (2)
- http://headless-service:8080/ | source: Introduction-to-Kubernetes-RU (2)
- https://auth0.com/blog/deployment-strategies-in-kubernetes/ | source: Introduction-to-Kubernetes-RU (2)
- https://www.dbbest.com/blog/column-oriented-database-technologies/ | source: RU_Clickhouse_lecture_2025
- https://www.tutorialspoint.com/dbms/dbms_indexing.htm | source: RU_Clickhouse_lecture_2025
- https://www.altinity.com/ | source: RU_Clickhouse_lecture_2025
- https://www.slideshare.net/profyclub_ru/clickhouse-77412233 | source: RU_Clickhouse_lecture_2025
- https://en.wikipedia.org/wiki/Log-structured_merge-tree | source: RU_Clickhouse_lecture_2025
- https://www.altinity.com/blog/2019/7/new-encodings-to-improve-clickhouse | source: RU_Clickhouse_lecture_2025
- https://nageshbattula.com/2018/08/06/oracle-sharding-18c-blog-post-series-2-pdb-sharding/ | source: RU_Clickhouse_lecture_2025
- https://makeomatic.ru/blog/2015/10/12/relational_database_2/ | source: RU_Clickhouse_lecture_2025
- https://www.altinity.com/blog/clickhouse-materialized-views-illuminated-part-1 | source: RU_Clickhouse_lecture_2025
- https://clickhouse.yandex/docs/en/operations/table_engines/kafka/ | source: RU_Clickhouse_lecture_2025
- https://clickhouse.com/ | source: Базы данных в MLOps
- https://hadoop.apache.org/docs/r1.2.1/hdfs_design.html | source: Базы данных в MLOps
- https://greenplum.org/ | source: Базы данных в MLOps
- https://spark.apache.org/downloads.html | source: Введение в Apache Spark
- http://localhost:4040/ | source: Введение в Apache Spark
- https://www.kaggle.com/parulpandey/palmer-archipelago-antarctica-penguin-data | source: Лабораторная работа 1 (весна 2026)
- https://www.kaggle.com/c/bike-sharing-demand | source: Лабораторная работа 1 (весна 2026)
- https://archive.ics.uci.edu/ml/datasets/Wine+Quality | source: Лабораторная работа 1 (весна 2026)
- https://www.kaggle.com/c/boston-housing | source: Лабораторная работа 1 (весна 2026)
- https://archive.ics.uci.edu/ml/datasets/Ionosphere | source: Лабораторная работа 1 (весна 2026)
- https://www.kaggle.com/zalando-research/fashionmnist | source: Лабораторная работа 1 (весна 2026)
- https://www.kaggle.com/c/dogs-vs-cats | source: Лабораторная работа 1 (весна 2026)
- https://www.kaggle.com/uciml/breast-cancer-wisconsin-data | source: Лабораторная работа 1 (весна 2026)
- https://www.kaggle.com/c/twitter-sentiment-analysis2 | source: Лабораторная работа 1 (весна 2026)
- https://www.kaggle.com/c/learn-ai-bbc | source: Лабораторная работа 1 (весна 2026)
- https://www.kaggle.com/uciml/sms-spam-collection-dataset | source: Лабораторная работа 1 (весна 2026)
- http://mmlab.ie.cuhk.edu.hk/projects/CelebA.html | source: Лабораторная работа 1 (весна 2026)
- https://arxiv.org/abs/1609.08675 | source: Лабораторная работа 1 (весна 2026)
- http://research.google.com/youtube8m/ | source: Лабораторная работа 1 (весна 2026)
- https://jmcauley.ucsd.edu/data/amazon/ | source: Лабораторная работа 1 (весна 2026)
- https://www.kaggle.com/ritesaluja/bank-note-authentication-uci-data | source: Лабораторная работа 1 (весна 2026)
- http://labelme.csail.mit.edu/Release3.0/index.php | source: Лабораторная работа 1 (весна 2026)
- https://archive.ics.uci.edu/ml/datasets/Connectionist+Bench+(Sonar,+Mines+vs.+Rocks | source: Лабораторная работа 1 (весна 2026)
- https://www.kaggle.com/uciml/pima-indians-diabetes-database | source: Лабораторная работа 1 (весна 2026)
- https://www.kaggle.com/jmcaro/wheat-seedsuci | source: Лабораторная работа 1 (весна 2026)
- https://www.kaggle.com/tunguz/200000-jeopardy-questions | source: Лабораторная работа 1 (весна 2026)
- https://www.kaggle.com/rodolfomendes/abalone-dataset | source: Лабораторная работа 1 (весна 2026)
- https://www.kaggle.com/c/fake-news/overview | source: Лабораторная работа 1 (весна 2026)
- https://image-net.org/ | source: Лабораторная работа 1 (весна 2026)
- https://www.hashicorp.com/product | source: Лабораторная работа 3 (весна 2026)
- https://habr.com/ru/articles/5366 | source: Лабораторная работа 3 (весна 2026)
- https://www.vaultproject.io/ | source: Лабораторная работа 3 (весна 2026)
- https://habr.com/ru/companies/ol | source: Лабораторная работа 3 (весна 2026)
- https://docs.ansible.com/ansible/lat | source: Лабораторная работа 3 (весна 2026)
- https://www.youtube.com/watch | source: Лабораторная работа 3 (весна 2026)
- https://kafka.apache.org/ | source: Лабораторная работа 4 (весна 2026)
- https://habr.com/ru/companies/southbridge/articles/550934/ | source: Лабораторная работа 4 (весна 2026)
- https://habr.com/ru/companies/nlmk/articles/682978/ | source: Лабораторная работа 4 (весна 2026)
- https://youtu.be/PtFTGQG2LwA | source: Лабораторная работа 4 (весна 2026)
- https://sparkbyexamples.com/pyspark/how-to-install-and-run-pyspark-on- | source: Лабораторная работа 5 (весна 2026)
- https://static.openfoodfacts.org/data/openfoodfacts- | source: Лабораторная работа 5 (весна 2026)
- https://world.openfoodfacts.org/data | source: Лабораторная работа 5 (весна 2026)
- https://sparkbyexamples.com/ | source: Лабораторная работа 5 (весна 2026)
- https://spark.apache.org/docs/latest/api/python/ | source: Лабораторная работа 5 (весна 2026)
- https://pythonru.com/biblioteki/pyspark-dlja-nachinajushhih | source: Лабораторная работа 5 (весна 2026)
- https://habr.com/ru/articles/708468/ | source: Лабораторная работа 5 (весна 2026)
- https://www.scala-lang.org/ | source: Лабораторная работа 7 (весна 2026)
- https://www.tutorialspoint.com/scala/scala_environment_setup.htm | source: Лабораторная работа 7 (весна 2026)
- https://laxfed.medium.com/data-analysis-with-scala-and-spark-part-1- | source: Лабораторная работа 7 (весна 2026)
- https://laxfed.medium.com/data-analysis-with-scala-and-spark-part-2- | source: Лабораторная работа 7 (весна 2026)
- https://alvinalexander.com/scala/scala-jdbc-connection-mysql-sql-select- | source: Лабораторная работа 7 (весна 2026)
- https://spark.apache.org/docs/latest/running-on-kubernetes.html | source: Лабораторная работа 8 (весна 2026)
- https://habr.com/ru/companies/neoflex/articles/511734/ | source: Лабораторная работа 8 (весна 2026)
- https://kubernetes.io/ru/docs/tutorials/kubernetes-basics/ | source: Лабораторная работа 8 (весна 2026)
- https://youtube.com/playlist?list=PLg5SS_4L6LYvN1RqaVesof8KAf- | source: Лабораторная работа 8 (весна 2026)
- https://mcs.mail.ru/blog/razvorachivanie-prilozhenie-na-apache-spark-v- | source: Лабораторная работа 8 (весна 2026)
- https://www.anaconda.com/products/distribution | source: Структура ML проекта
- https://github.com/drivendata/cookiecutter-data-science | source: Структура ML проекта
- https://drivendata.github.io/cookiecutter-data-science/ | source: Структура ML проекта
- https://github.com/surfstudio/ocean | source: Структура ML проекта
- https://github.com/surfstudio/ocean/blob/master/README_ru | source: Структура ML проекта
- https://github.com/catalyst-team/catalyst | source: Структура ML проекта
- https://catalyst-team.github.io/catalyst/ | source: Структура ML проекта
- https://dvc.org/doc | source: Структура ML проекта
- https://docs.docker.com/ | source: Структура ML проекта
- https://www.docker.com/products/docker- | source: Структура ML проекта
- https://www.jenkins.io/doc/book/ | source: Структура ML проекта

## Файлы из Telegram-экспорта

- 2026-02-09T15:05:16: `(File exceeds maximum size. Change data exporting settings to download.)` (application/zip) - 1 занятие
- 2026-02-13T09:37:48: `files/Лабораторная работа 1 (весна 2026).pdf` (application/pdf) - Лабораторная 1, варианты проставлены в сводке курса
- 2026-02-13T19:21:13: `files/BD_2026_1.pdf` (application/pdf) - 1 лекция
- 2026-03-18T18:24:20: `files/Лабораторная работа 2 (весна 2026).pdf` (application/pdf) - Лабораторная работа 2
- 2026-03-18T18:24:33: `files/Лабораторная работа 3 (весна 2026).pdf` (application/pdf) - Лабораторная работа 3
- 2026-03-18T18:24:48: `files/Лабораторная работа 4 (весна 2026).pdf` (application/pdf) - Лабораторная работа 4
- 2026-04-15T13:32:41: `files/Структура ML проекта.pdf` (application/pdf) - 
- 2026-04-15T13:32:41: `files/Базы данных в MLOps.pdf` (application/pdf) - 
- 2026-04-15T13:32:41: `files/apache kafka ru.pdf` (application/pdf) - Материалы прошедших лекций
- 2026-04-15T18:32:39: `files/Лабораторная работа 5 (весна 2026).pdf` (application/pdf) - 5 лабораторная работа
- 2026-04-17T18:22:09: `files/Введение в Apache Spark.pdf` (application/pdf) - 5 лекция
- 2026-04-24T19:23:47: `files/Лабораторная работа 6 (весна 2026).pdf` (application/pdf) - Лабораторная работа №6
- 2026-04-29T18:48:55: `files/Лабораторная работа 7 (весна 2026).pdf` (application/pdf) - 7 лабораторная работа
- 2026-05-04T19:51:01: `files/RU_Clickhouse_lecture_2025.pdf` (application/pdf) - 6 лекция
- 2026-05-29T20:21:59: `files/Лабораторная работа 8 (весна 2026).pdf` (application/pdf) - 8 Лабораторная работа
- 2026-06-11T18:59:46: `files/Список вопросов ИБД весна 2026.pdf` (application/pdf) - Вопросы к экзамену
- 2026-06-11T19:00:17: `files/Introduction-to-Kubernetes-RU (2).pdf` (application/pdf) - 7 лекция
- 2026-06-11T19:00:45: `files/1 Intro_ETL_HDFS_ZooKeeper_Spark-overview (4).pdf` (application/pdf) - 8 лекция (суммаризация)