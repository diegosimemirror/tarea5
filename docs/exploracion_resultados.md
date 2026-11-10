# Resultados de la exploración (salida en bruto)

## 1. Tamaño del detalle (filas, columnas)

```
(150641, 68)
```

## 2. Columnas

```
NIVEL, SECTOR, ENTIDAD, CODIGO_UNICO, CODIGO_SNIP, NOMBRE_INVERSION, NOMBRE_OPMI, NOMBRE_UF, NOMBRE_UEI, SEC_EJEC, NOMBRE_UEP, ESTADO, SITUACION, MONTO_VIABLE, COSTO_ACTUALIZADO, CTRL_CONCURR, MONTO_LAUDO, MONTO_FIANZA, ALTERNATIVA, FECHA_REGISTRO, FECHA_VIABILIDAD, FUNCION, PROGRAMA, SUBPROGRAMA, MARCO, TIPO_INVERSION, DES_MODALIDAD, REGISTRADO_PMI, PMI_ANIO_1, PMI_ANIO_2, PMI_ANIO_3, PMI_ANIO_4, EXPEDIENTE_TECNICO, INFORME_CIERRE, TIENE_F9, FEC_REG_F9, ETAPA_F9, PRIMER_DEVENGADO, ULTIMO_DEVENGADO, DEVEN_ACUMUL_ANIO_ANT, DEV_ANIO_ACTUAL, PIA_ANIO_ACTUAL, PIM_ANIO_ACTUAL, CERTIF_ANIO_ACTUAL, COMPROM_ANUAL_ANIO_ACTUAL, SALDO_EJECUTAR, TIENE_F8, ETAPA_F8, TIENE_F12B, TIENE_AVAN_FISICO, AVANCE_FISICO, AVANCE_EJECUCION, ULT_FEC_DECLA_ESTIM, DES_TIPOLOGIA, IND_IOARR_EMERG, DEPARTAMENTO, PROVINCIA, DISTRITO, UBIGEO, LATITUD, LONGITUD, FEC_INI_EJECUCION, FEC_FIN_EJECUCION, FEC_INI_EJEC_FISICA, FEC_FIN_EJEC_FISICA, NUM_HABITANTES_BENEF, MONTO_ET_F8, ANIO_PROCESO
```

## 3. Tres filas al azar (columnas clave)

```
      NIVEL                SECTOR                             ENTIDAD CODIGO_UNICO                                                                                                                                                                                                                                                                                                                                                              NOMBRE_INVERSION COSTO_ACTUALIZADO    FEC_FIN_EJECUCION
26124    GR  GOBIERNOS REGIONALES          GOBIERNO REGIONAL AMAZONAS      2304343                                                                                                                                                                                                                                         MEJORAMIENTO DE LA CAPACIDAD DE  ATENCION NEONATAL DEL C.S JAMALCA- DISTRITO DE JAMALCA DE LA PROVINCIA DE UTCUBAMBA- REGION AMAZONAS          198687.8                     
60898    GL     GOBIERNOS LOCALES  MUNICIPALIDAD DISTRITAL DE LUCANAS      2731271  ADQUISICION DE TERRENO EN EL(LA) EN LA LOCALIDAD DE LUCANAS, PARA EL  MEJORAMIENTO Y AMPLIACION DEL SERVICIO DE AGUA POTABLE URBANO Y MEJORAMIENTO Y AMPLIACION DEL SERVICIO DE ALCANTARILLADO Y CREACION DEL SERVICIO DE TRATAMIENTO DE AGUAS RESIDUALES PARA DISPOSICIÓN FINAL EN EL CENTRO POBLADO LUCANAS, DISTRITO DE LUCANAS, PROVINCIA LUCANAS, DEPARTAMENTO AYACUCHO          173080.0  2026-10-01 00:00:00
23818    GL     GOBIERNOS LOCALES    MUNICIPALIDAD DISTRITAL DE CASCA      2722291                                                                                                                                                                                                                 CONSTRUCCION DE SERVICIOS HIGIENICOS Y/O VESTIDORES EN EL(LA) I.E. SAN ANTONIO DE PADUA  DISTRITO DE CASCA, PROVINCIA MARISCAL LUZURIAGA, DEPARTAMENTO ANCASH         310721.33  2026-10-02 00:00:00
```

## 4. CUI duplicados en el detalle

```
67
```

## 5. Celdas vacías por columna en gobierno nacional (de 12731)

```
FEC_REG_F9                   11132
ETAPA_F9                     11132
CERTIF_ANIO_ACTUAL            9356
PIA_ANIO_ACTUAL               9356
COMPROM_ANUAL_ANIO_ACTUAL     9356
PMI_ANIO_1                    7915
AVANCE_FISICO                 7681
PMI_ANIO_4                    7608
PMI_ANIO_3                    7608
PMI_ANIO_2                    7608
NUM_HABITANTES_BENEF          6435
ALTERNATIVA                   6430
ULT_FEC_DECLA_ESTIM           6194
ULTIMO_DEVENGADO              5427
PRIMER_DEVENGADO              5427
DES_TIPOLOGIA                 4781
AVANCE_EJECUCION              3781
MONTO_ET_F8                   3114
FEC_FIN_EJEC_FISICA           2755
FEC_INI_EJEC_FISICA           2755
ETAPA_F8                      1740
NOMBRE_OPMI                   1622
NOMBRE_UF                     1355
FEC_INI_EJECUCION             1296
FEC_FIN_EJECUCION             1296
DES_MODALIDAD                  964
NOMBRE_UEI                     292
LATITUD                        159
LONGITUD                       158
UBIGEO                         137
MONTO_VIABLE                    22
FECHA_VIABILIDAD                21
DISTRITO                        17
NOMBRE_UEP                      15
PROVINCIA                       15
DEPARTAMENTO                    12
CODIGO_UNICO                    11
SEC_EJEC                         3
```

## 6a. Valores que no son número (sin contar vacíos)

```
MONTO_VIABLE             0
COSTO_ACTUALIZADO        0
DEVEN_ACUMUL_ANIO_ANT    0
DEV_ANIO_ACTUAL          0
PIM_ANIO_ACTUAL          0
SALDO_EJECUTAR           0
AVANCE_FISICO            0
AVANCE_EJECUCION         0
NUM_HABITANTES_BENEF     0
LATITUD                  0
LONGITUD                 0
```

## 6b. Estadísticos de montos en gobierno nacional (soles)

```
                         count        mean          std         min       25%        50%         75%           max
MONTO_VIABLE           12709.0  39272092.5  536091442.9         1.0  363358.7  2535045.0   9752953.0  3.055270e+10
COSTO_ACTUALIZADO      12731.0  48789862.0  562391973.8         0.0  434701.0  3002920.2  13235776.3  3.052714e+10
DEVEN_ACUMUL_ANIO_ANT  12731.0  10604520.6  117286394.8         0.0       0.0    34908.2   1652576.6  1.137953e+10
DEV_ANIO_ACTUAL        12731.0    907845.4   13686964.7         0.0       0.0        0.0         0.0  1.302690e+09
PIM_ANIO_ACTUAL        12731.0   1278510.6   15835146.2         0.0       0.0        0.0         0.0  1.335479e+09
SALDO_EJECUTAR         12731.0  37104367.7  532688164.7 -26606395.7   60000.0   796339.2   6682598.1  3.055270e+10
AVANCE_FISICO           5050.0        83.1        948.5         0.0      40.3       89.8       100.0  6.741800e+04
AVANCE_EJECUCION        8950.0        50.9        737.0         0.0       0.0        7.4        90.3  6.656080e+04
NUM_HABITANTES_BENEF    6296.0    419883.3    5921871.0         0.0     474.0     2392.0     19977.2  3.413323e+08
LATITUD                12572.0        62.6       7216.3    -32400.0     -12.1       -8.3         0.0  8.002130e+05
LONGITUD               12573.0       604.1      73069.5      -800.6     -77.5      -75.3         0.0  8.192755e+06
```

## 6c. Montos en cero o negativos

```
                        cero  negativo
MONTO_VIABLE               0         0
COSTO_ACTUALIZADO         21         0
DEVEN_ACUMUL_ANIO_ANT   5687         0
DEV_ANIO_ACTUAL        10196         0
PIM_ANIO_ACTUAL         9687         0
SALDO_EJECUTAR           582       349
AVANCE_FISICO            538         0
AVANCE_EJECUCION        3786         0
NUM_HABITANTES_BENEF      36         0
LATITUD                 3297      9269
LONGITUD                3297      9272
```

## 7. Frecuencias de NIVEL (gobierno nacional)

```
NIVEL
GN    12731
```

## 7. Frecuencias de ESTADO (gobierno nacional)

```
ESTADO
ACTIVO    12731
```

## 7. Frecuencias de SITUACION (gobierno nacional)

```
SITUACION
VIABLE            6442
APROBADO          6268
EN FORMULACION      21
```

## 7. Frecuencias de MARCO (gobierno nacional)

```
MARCO
INVIERTE    9651
SNIP        3080
```

## 7. Frecuencias de TIPO_INVERSION (gobierno nacional)

```
TIPO_INVERSION
INVERSIONES IOARR        4826
PROYECTO DE INVERSION    3233
PIP MAYOR (SNIP)         2628
INTERVENCIONES IRI       1442
PIP MENOR (SNIP)          425
PROYECTO EMBLEMATICO      112
PROGRAMA DE INVERSION      27
PROGRAMA (SNIP)            27
PROYECTO ENERGIA            4
PROYECTO ESSALUD            4
PROYECTO SANEAMIENTO        2
PROYECTO PEIP               1
```

## 7. Frecuencias de DES_MODALIDAD (gobierno nacional)

```
DES_MODALIDAD
ADMINISTRACIÓN INDIRECTA - POR CONTRATA                                               7079
ADMINISTRACIÓN DIRECTA                                                                1466
                                                                                       964
ADMINISTRACIÓN DIRECTA,ADMINISTRACIÓN INDIRECTA - POR CONTRATA                         858
ADMINISTRACIÓN INDIRECTA - POR CONTRATA,ADMINISTRACIÓN DIRECTA                         745
ADMINISTRACIÓN INDIRECTA - NÚCLEO EJECUTOR                                             664
ADMINISTRACIÓN INDIRECTA - POR CONTRATA,ADMINISTRACIÓN INDIRECTA - NÚCLEO EJECUTOR     209
ADMINISTRACIÓN INDIRECTA - NÚCLEO EJECUTOR,ADMINISTRACIÓN INDIRECTA - POR CONTRATA     176
ADMINISTRACIÓN INDIRECTA - ASOCIACIÓN PÚBLICA PRIVADA (APP)                             92
ADMINISTRACIÓN INDIRECTA - ASOCIACIÓN PUBLICA PRIVADA (APP)                             82
ADMINISTRACIÓN INDIRECTA - OBRAS POR IMPUESTOS                                          61
ADMINISTRACIÓN INDIRECTA - CONCURSO OFERTA                                              53
```

## 7. Frecuencias de TIENE_F12B (gobierno nacional)

```
TIENE_F12B
SI    9099
NO    3632
```

## 7. Frecuencias de EXPEDIENTE_TECNICO (gobierno nacional)

```
EXPEDIENTE_TECNICO
SI    9182
NO    3549
```

## 7. Frecuencias de INFORME_CIERRE (gobierno nacional)

```
INFORME_CIERRE
NO    12731
```

## 7. Frecuencias de REGISTRADO_PMI (gobierno nacional)

```
REGISTRADO_PMI
NO    7608
SI    5123
```

## 7. Frecuencias de ANIO_PROCESO (gobierno nacional)

```
ANIO_PROCESO
2026    12731
```

## 8a. Sectores únicos con espacios dobles o al final

```
['CONSEJO NACIONAL  DE LA MAGISTRATURA', 'DEFENSORIA  DEL PUEBLO']
```

## 8b. Número de entidades por sector

```
SECTOR
EDUCACION                                             57
FONAFE                                                26
PRESIDENCIA DEL CONSEJO DE MINISTROS                  18
PRODUCCION                                             8
AMBIENTAL                                              7
ECONOMIA Y FINANZAS                                    7
TRANSPORTES Y COMUNICACIONES                           7
AGRICULTURA Y RIEGO                                    6
MUJER Y POBLACIONES VULNERABLES                        6
VIVIENDA, CONSTRUCCION Y SANEAMIENTO                   6
UNIVERSIDADES                                          5
ENERGIA Y MINAS                                        4
JUSTICIA                                               4
DEFENSA                                                4
CULTURA                                                4
SALUD                                                  3
DESARROLLO E INCLUSION SOCIAL                          2
TRABAJO Y PROMOCION DEL EMPLEO                         2
INTERIOR                                               2
CONTRALORIA GENERAL                                    1
ESSALUD                                                1
CONSEJO NACIONAL  DE LA MAGISTRATURA                   1
CONGRESO DE LA REPUBLICA                               1
DEFENSORIA  DEL PUEBLO                                 1
COMERCIO EXTERIOR Y TURISMO                            1
FUERO MILITAR POLICIAL                                 1
PODER JUDICIAL                                         1
JURADO NACIONAL DE ELECCIONES-JNE                      1
MINISTERIO PUBLICO                                     1
OFICINA NACIONAL DE PROCESOS ELECTORALES-ONPE          1
RELACIONES EXTERIORES                                  1
REGISTRO NACIONAL DE IDENTIFICACION Y ESTADO CIVIL     1
TRIBUNAL CONSTITUCIONAL                                1
```

## 9. Rango de FECHA_VIABILIDAD

```
mín 2001-08-15 00:00:00 | máx 2026-11-06 00:00:00 | vacías o inválidas 21 | después de 2040: 0
```

## 9. Rango de FEC_INI_EJECUCION

```
mín 2001-10-16 00:00:00 | máx 2069-12-31 00:00:00 | vacías o inválidas 1296 | después de 2040: 7
```

## 9. Rango de FEC_FIN_EJECUCION

```
mín 2005-01-27 00:00:00 | máx 2047-02-01 00:00:00 | vacías o inválidas 1296 | después de 2040: 5
```

## 9b. Fin de ejecución ya vencido y sin informe de cierre

```
5122
```

## 10a. Las 15 inversiones más caras del gobierno nacional

```
                                      SECTOR CODIGO_UNICO        _costo         TIPO_INVERSION                                                                  NOMBRE_INVERSION
50063           TRANSPORTES Y COMUNICACIONES      2655396  3.052714e+10  PROYECTO DE INVERSION  CREACION DEL SERVICIO FERROVIARIO INTERURBANO EN SAN JUAN DE MARCONA ¿ ANDAHUAYL
59878           TRANSPORTES Y COMUNICACIONES      2623129  2.538224e+10  PROYECTO DE INVERSION  CREACION DEL SERVICIO DE TRANSITABILIDAD VIAL INTERURBANA EN LA NUEVA CARRETERA 
7550            TRANSPORTES Y COMUNICACIONES      2655431  2.449171e+10  PROYECTO DE INVERSION  CREACION DEL SERVICIO FERROVIARIO INTERURBANO EN EL FERROCARRIL LIMA ¿ ICA, DIST
77514           TRANSPORTES Y COMUNICACIONES      2300242  2.356931e+10  PROYECTO DE INVERSION  CREACION DE LA LINEA 3 DE LA RED BASICA DEL METRO DE LIMA, PROVINCIA DE LIMA, DE
143476          TRANSPORTES Y COMUNICACIONES      2233850  1.710514e+10       PIP MAYOR (SNIP)  CONSTRUCCION DE LA LINEA 2 Y RAMAL AV. FAUCETT-GAMBETTA DE LA RED BASICA DEL MET
58720                    ECONOMIA Y FINANZAS      2408189  1.517342e+10       PIP MAYOR (SNIP)           CONSTRUCCION DEL ANILLO VIAL PERIFÉRICO  DE LA CIUDAD DE LIMA  Y CALLAO
99183                    ECONOMIA Y FINANZAS      2721232  1.418867e+10  PROYECTO DE INVERSION  MEJORAMIENTO Y AMPLIACIÓN DEL SERVICIO DE TRANSPORTE URBANO EN LÍNEA 1 DEL METRO
101016          TRANSPORTES Y COMUNICACIONES      2338387  1.261510e+10  PROYECTO DE INVERSION  CREACION DE LA LINEA 4 DEL METRO DE LIMA Y CALLAO, PROVINCIAS DE LIMA Y CALLAO, 
126679  PRESIDENCIA DEL CONSEJO DE MINISTROS      2667637  7.798852e+09  PROYECTO DE INVERSION  MEJORAMIENTO Y AMPLIACION DEL SERVICIO DE DRENAJE PLUVIAL EN LOS DISTRITOS DE PI
16592                                 FONAFE      2494846  6.087615e+09  PROYECTO DE INVERSION  MEJORAMIENTO Y AMPLIACION DE LOS SERVICIOS DE AGUA POTABLE Y ALCANTARILLADO EN L
143480          TRANSPORTES Y COMUNICACIONES      2190272  4.482801e+09       PIP MAYOR (SNIP)  MEJORAMIENTO Y AMPLIACION DEL SERVICIO AEROPORTUARIO EN LA REGION CUSCO MEDIANTE
31004           TRANSPORTES Y COMUNICACIONES      2619648  3.563162e+09  PROYECTO DE INVERSION  CREACION DEL SERVICIO DE TRANSITABILIDAD VIAL INTERURBANA EN VIA DE EVITAMIENTO 
121263                                 SALUD      2654533  3.369860e+09  PROYECTO DE INVERSION  MEJORAMIENTO Y AMPLIACION DE ATENCIÓN DE SERVICIOS DE SALUD HOSPITALARIOS EN HOS
2730                                  FONAFE      2412780  3.177457e+09  PROYECTO DE INVERSION  MEJORAMIENTO DEL SERVICIO DE ALCANTARILLADO EN AREA DE DRENAJE DEL COLECTOR SURC
110469          TRANSPORTES Y COMUNICACIONES      2234983  3.062923e+09       PIP MAYOR (SNIP)    REHABILITACION Y MEJORAMIENTO DE LA CARRETERA DV. CERRO DE PASCO - TINGO MARIA
```

## 10b. Avance físico o de ejecución mayor a 100 %

```
físico: 17 | ejecución: 11
```

## 10c. Coordenadas faltantes o en cero (no se pueden mapear)

```
3456
```

## 10d. Caracteres mal codificados (Ã, �) en nombres

```
0
```

## 11. Brechas: tamaño, columnas y ejemplo

```
(505452, 9)
['CODIGO_UNICO', 'DES_SERVICIO', 'DES_BRECHA', 'DES_UM', 'ESPACIO_GEOGRAFICO', 'ANIO', 'VALOR', 'CONTRIBUCION', 'ANIO_PROC']
  CODIGO_UNICO                                     DES_SERVICIO                                                                                                      DES_BRECHA                                    DES_UM ESPACIO_GEOGRAFICO    ANIO VALOR CONTRIBUCION ANIO_PROC
0      2437250                   SERVICIO DE EDUCACIÓN PRIMARIA  PORCENTAJE DE LOCALES EDUCATIVOS CON EDUCACIÓN PRIMARIA QUE CONTIENE CAPACIDAD INSTALADA INADECUADA (LEEPCII).                               PERSONA/AÑO          DISTRITAL  2019.0   9.8          1.0      2026
1      2612960    SERVICIO DE PRÁCTICA DEPORTIVA Y/O RECREATIVA                              PORCENTAJE DE INSTALACIONES DEPORTIVAS Y /O RECREATIVAS EN CONDICIONES INADECUADAS  INSTALACIONES DEPORTIVAS Y/O RECREATIVAS               OTRO                      620.0      2026
2      2436836  SERVICIO DE INTEGRACIÓN Y SOSTENIBILIDAD URBANA     PORCENTAJE DE LA POBLACIÓN URBANA CON INADECUADA INFRAESTRUCTURA PARA EL ESPARCIMIENTO E INTEGRACIÓN URBANA                        POBLACIÓN ATENDIDA          DISTRITAL  2019.0   0.0         15.0      2026
```

## 11b. Brechas por inversión (cuántas filas tiene cada CUI)

```
count    322155.00
mean          1.57
std           0.91
min           1.00
25%           1.00
50%           1.00
75%           2.00
max         269.00
```

## 11c. Inversiones de gobierno nacional con al menos una brecha

```
10046 de 12731
```

## 11d. Frecuencias de ESPACIO_GEOGRAFICO

```
ESPACIO_GEOGRAFICO
DISTRITAL        310532
OTRO             136129
PROVINCIAL        24942
DEPARTAMENTAL     17071
NACIONAL          16778
```

## 11d. Frecuencias de ANIO

```
ANIO
          503793
2019.0      1396
0.0          199
2020.0        30
2018.0        13
2029.0         7
2021.0         5
2022.0         2
2038.0         2
2028.0         2
```

## 11d. Frecuencias de DES_UM

```
DES_UM
PERSONAS                                             124191
KM                                                    70578
INSTALACIÓN EDUCATIVA                                 34378
M2                                                    30226
INSTALACIONES DEPORTIVAS Y/O RECREATIVAS              26029
HA                                                    22801
ESTABLECIMIENTO DE SALUD                              21613
UNIDAD DE MEDIDA POR DEFINIR                          20475
SERVICIOS OPERATIVOS O MISIONALES INSTITUCIONALES     18866
LOCAL EDUCATIVO                                       17523
```

## 11e. Estadísticos de VALOR (tamaño de la brecha) y CONTRIBUCION

```
             VALOR  CONTRIBUCION
count      1645.00     505255.00
mean     129961.54       6717.66
std     2151613.87     344641.16
min           0.00      -2440.00
25%           1.00          1.00
50%          46.00         10.00
75%         100.80        219.00
max    57885873.00   71472078.00
```

## 11f. VALOR mayor a 100 (no puede ser porcentaje)

```
412
```

## 11g. Filas duplicadas exactas en brechas

```
0
```

## 12. Formato 12-B: tamaño y duplicados

```
(227566, 8) | CUI duplicados: 0
```

## 12b. Estados en el 12-B

```
ESTADO
ACTIVO                    115902
CERRADO                    54799
DESACTIVADO TEMPORAL       34864
DESACTIVADO PERMANENTE     22001
```

## 12c. Fecha de la última actualización del 12-B

```
mín 2018-05-03 00:00:00 | máx 2026-11-08 23:01:30 | vacías 1132
```

## 12d. Inversiones de gobierno nacional con fila en el 12-B

```
9373 de 12731
```

## 12e. Textos no vacíos (gobierno nacional)

```
{'ULT_ESTADO_SITUACIONAL': 8912, 'ULT_PROBLEMA': 8249, 'ACC_PROBLEMA': 8250}
```

## 12f. Ejemplos de ULT_PROBLEMA

```
74      [04/09/2026] NO SE PRESENTAN PROBLEMAS EN LA G...
3317    [27/08/2026] A ESPERA DE LA APROBACIÓN DE PROP...
3474    [12/02/2026] NINGUNA. AL SER UN PROYECTO RECIE...
3764    [01/10/2026] no hay restricciones. SE SOLICITÓ...
3777    [17/09/2026] por el momento no cuenta con disp...
4478    [08/04/2026] en la actualidad no se identifico...
4479    [15/10/2026] OBSERVACIONES QUE COMPRENDEN ASPE...
5135                 [27/01/2026] INCORPORACION INOP 2027
```