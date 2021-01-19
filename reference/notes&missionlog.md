### 2020/11/15

* 字符串用法：`string.lower()`全部改为小写。

* np.loadtxt()函数：
  -  `fname`要读取的文件、文件名、或生成器。
  -  `dtype`数据类型，默认float。
  -  `comments`注释。如果开头是#，这一行不被读取。
  -  `delimiter`分隔符，默认是空格。
  -  `skiprows`跳过前几行读取，默认是0，必须是int整型。
  -  `usecols`：要读取哪些列，0是第一列。例如，usecols = （1,4,5）将提取第2，第5和第6列。默认读取所有列。
  -  `unpack`如果为`True`，将分列读取。
```python
loadtxt(fname, dtype=, comments='#', delimiter=None, converters=None, skiprows=0, usecols=None, unpack=False, ndmin=0)
```

* 1e-100，这个用法就是10^-100^
* 初步编码规范：空格和空行。pycharm中使用Alt+Ctrl+L快捷键。
* 问：*时间的输入方式是否合适？不如直接输入标准时间格式，类似`'2020-10-20 17:00:00'`这种*。
* *typo：line 86: # for interpolation*
* 建议：*line 98: `n = len(orb_time)`这个命名会不会有点过于随意了……*
* 编号：46838。https://www.n2yo.com/?s=43663|46838
* **指令序列已出，请尽快联络**。
***
### 2020/11/16
* scipy.interpolate.griddata
```python
scipy.interpolate.griddata(points, values, xi, method='linear', fill_value=nan, rescale=False)
```
Parameters :

points: 2-D ndarray of floats with shape (n, D), or length D tuple of 1-D ndarrays with shape (n,).
Data point coordinates.

values: ndarray of float or complex, shape (n,)
Data values.

xi: 2-D ndarray of floats with shape (m, D), or length D tuple of ndarrays broadcastable to the same shape.
Points at which to interpolate data.

method: {‘linear’, ‘nearest’, ‘cubic’}, optional

Returns: ndarray
Array of interpolated values. 

* 所以为什么选用linear而不是cubic?



* get_sun
* SkyCoord
* 再记一边：right ascension赤经，declination赤纬。
所以下面这个算地球的radec是怎么回事？**这里面的天球坐标究竟是怎么定义的？**
```python
earth_ra = orb_ra + np.pi
earth_dec = -orb_dec
```
已解决：相当于在卫星看来地球的位置，可以把卫星和地球认为都在原点，这样的话把原点移到卫星上也不会改变远处天体的RA DEC. by the way, 天球坐标使用的是J2000标准

* 纠错：line 109出现一个逗号
* 疑问：关于plfunc.angular_distance函数
如果目的是计算两点之间的夹角的话，也不是这么算的啊？比如可以用向量点乘。
```python
# calcualte the angular separation on the sphere
def angular_distance(ra1, dec1, ra2, dec2):
    # input and output radians
    cos_sep = np.sin(dec1) * np.sin(dec2) + np.cos(dec1) * np.cos(dec2) * np.cos(ra1 - ra2)
    # sep in [0, pi]
    sep = np.arccos(cos_sep)

    return sep
```
*已解决*。弄错了，天球纬度是+90~-90，和球坐标不一样，它是对的。

* line 124: occultation_angle掩星角，不就是90度吗……写那个式子的用意不理解。solved
* 疑问：line 130`good_visibility = earth_angle > earth_occultation_angle`, 为什么earth_occultation_angle这个角不应该是45度？solved
* 变量tt就是一个np浮点数，值等于orb_time。
* line 142: good_grid指的是？为什么在目标被遮挡的时候取1？solved
*  Find在当前文件查找，快捷键为**Ctrl + F** 
*  中间的一系列bool变量都是0和1的数组，不是一个数。其实有点晕。

### 2020/11/17
*  通过find_continous_intervals和Is_too_short两个函数折腾完之后，得到观测目标可行的开始、结束的时间序列的index。line 148, 弄了很久才理解。
*  那个问题出现了很多次，就是为什么grid相关的单独又处理了一次？solved
*  程序中是否做了类似把最后计算出来的时间和转向操作等以一种易读的方式输出，来得到一个直观的观测计划，这种？*已提上日程*。
*  上面那些其实算作是16日深夜的工作。今晚折腾gitub花了好一会儿，只不过基本也算会用了。接触新事物都这样没差。
*  *所以有个小问题，所有**以上**提及行数的，现在都指的是11-15版本程序里的*。
*  `~`是按位取反。

### 2020/11/18
* -y指的是太阳能电池板法线方向。
* st: star tracker星敏。一个类似拍照的设备，用于精确的姿态确定。在很多情况下都不工作。
* install package: pyquaternion-0.9.9
* 四元数计算的结果是一个角度，而非转向。这个角度发送后，卫星通过其他方式（我们不关心）可以调整到这个要求的姿态。这是工作机制。
* 今日的微信群消息已记录。之后看懂程序再研究。
* HV是什么的缩写？high voltage
* 今日试运行：已检查至开机时间计算部分，认为三部分时间计算有效：可观测时间（目标在地球遮挡外+可控制）、可姿控时间（有卫星使用权但观测角度被地球遮挡）、无控制时间。得到系列输出i为轨道时间序列orb_time的对应index。
* **疑问**：遮挡角度计算：np.arcsin((R_earth + h_atm) / h_sat)这个写的应该是对的，感觉1不对吧！
* *以上是17日深夜工作*。
* 上面那个疑问，这里采用了一点近似，因为轨道高度相比半径是小量。其实没损失多少精度。*还是要好好睡觉……早上瞬间就懂了*
* when blocked: grid_target，使用虚拟目标。如果是以卫星为原点的天球坐标系，虚拟元应该就是背对地球的方向吧？*待确认* line 159
* Q: 在可以姿控的时间内是不是不需要考虑转向损耗，想怎么转就怎么转？比如目标被遮挡，就看天或者看其他目标，总之把开机观测时间尽可能延长？
* 探测器轴z、太阳能板法线y（应该是垂直的吧），两轴的方向确定卫星姿态。
* **卫星坐标系**问题：见图片satellite coordinate.png, 星敏自身的指向为(0,0,1), 用安装矩阵乘以它得到卫星坐标系中的指向：(0,sin18,-cos18). 此外，探测器指向为-z，太阳能板法线为y。
* pl.radec_to_xyz函数就是球坐标系，球面r=1的坐标变换。
* np.cross函数：计算叉乘。

### 20201119
* func.py里面的函数calcualte_qparm名字打错了……*嗯，11/27证实已经改回来了，学长细啊*。
* 四元数的再学习：
	* 基本介绍：四元数都是由实数加上三个虚数单位 i、j、k 组成，而且它们有如下的关系： i^2 = j^2 = k^2 = -1， i^0 = j^0 = k^0 = 1 , 每个四元数都是 1、i、j 和 k 的线性组合，即是四元数一般可表示为a + bi+ cj + dk。对于i、j、k本身的几何意义可以理解为一种旋转，其中i旋转代表XY平面中X轴正向向Y轴正向的旋转，j旋转代表XZ平面中Z轴正向向X轴正向的旋转，k旋转代表YZ平面中Y轴正向向Z轴正向的旋转。

### 20201122
* 先暂且跳过这两个核心函数：

	* possible_st_pointings_new
	* select_st_radec_new

* 大框架今天已经看完了。问题就在于这两个函数具体是怎样工作的。弄清楚之后基本上就可以理解了。后面的基本是把几何计算结果转化成指令、图形输出这类的。

### 20201127
* 天呐……几日不见，面目全非。当从头开始……
* get_data_trans函数把日期记为2020-11-18T这种形式的意思是？
* 注：import 里面的re, struct, binascii三个库都是没有用上的，可以删去。
* 建议最后把没有用的代码和注释删去，整理格式。
* 我这里再次总结一遍：interpolate.griddata这个插值函数的效果，简单来说就是把SAA标准地图上面的辐射值给投射到实际的轨道文件的对应坐标点上。使用了线性插值。这我在1127的test文件中以print进行了标注。
* 这……那些筛选方案修改得太快了吧。之后准备直接问zyc本人好了。那么这两天先解决几何问题吧。
* 四元数旋转的简单应用：对于一个xyz向量(x, y, z), 以这个向量为轴旋转θ角，对应的四元数：cos(θ/2)+xsin(θ/2)·i+ysin(θ/2)·j+zsin(θ/2)·k. 把一个点w=(wx, wy, wz)进行这个旋转操作，就是qw'=q·qw·q^-1^. qw和qw'都是纯四元数，即实部为零，后三项对应的是xyz坐标。
* 好，以下进入possible_st_pointings_new函数。

	* mid的叉乘乘出来是个什么啊？*疑问保留*。
	* map() 会根据提供的函数对指定序列做映射。`map(function, iterable, ...)`第一个参数 function 以参数序列中的每一个元素调用 function 函数，返回包含每次 function 函数返回值的新列表。返回值是map object类型。
	* Quaternion这个函数生成的旋转四元数就是上面的补充知识说的这一个。但是……为什么我试用下来它应该是以弧度制来接受'angle'的参数的？对没错就是这样，*这里有问题*。
	* 旋转操作.rotate不明。网上查不到文档和出处。内部查找结果，比较可信的是rotate(self, vector)方法。根据观察，它极大可能就是上面四元数知识里面的这种旋转。把这个输入向量按照四元数旋转操作旋转。输出结果为旋转后的向量。
	* 20201128以下。首先，四元数计算操作确认。Quaternion和rotate的用法就是上面写的那样。
	* mid_rot变量想要实现的应该是将mid向量绕目标所在的坐标（天球坐标）与原点所构成的旋转轴，旋转x角度。x从0到360，每10度算一次，一共36个。
	* np.linspace等差数列函数。相当于range(). 三个参数分别是start, end, length. 输出结果类型是np.ndarray.
	* 注意，文件里面的ra-dec都是转换成了弧度的。np的相关计算基本都是基于弧度的，比如sin, cos.
	* quat0里面的是一些四元数，分别对应36个mid_rot向量作为旋转轴，旋转角为（大概）卫星坐标系和天球坐标系的夹角w依次加上一些角度（0到15度，共五个），总计长度为180。
	* `quat = Quaternion(axis=target_pos_xyz, angle=i)`这个地方的angle又用成角度了，*应该转换成弧度*。
	* quat_r，把旋转变换成了quat·quat0的四元数。嗯……不确定这个计算的意义。似乎正式四元数的知识有欠缺。*需要问一下*。
	* 最后的输出就是detector&solar panet指向的一个序列。
	* 好那么这就算结束了这个函数，遗留了几个问题，应该是已经用斜体标注出来了。
	* 20201129注：角度问题已经修改。

***

### 20201129
* 现在主程序里面新加的框架的people这一部分不太理解。
* 关于时间问题：北京时间、utc、unix的区分：utc( Universal Time Coordinated ), 协调世界时。一种统一计时法。据unix时间戳词条介绍，Unix时间戳（英文为Unix epoch, Unix time, POSIX time 或 Unix timestamp）是从1970年1月1日（UTC/GMT的午夜）开始所经过的秒数，不考虑闰秒。北京时间与utc应该是相差八个时区。
* 直接从轨道文件中读取的orb_time_bj的格式是2020-11-18T23:59:50.000这种类型。后面的orb_time操作将其减去8个小时，并且转换成unix秒数格式，成为utc的标准形式。
* 接昨天，计算出detector&solar panet指向后，func.calc_st_radec计算星敏的指向，有一个18度夹角，比较简单。
* calculate_sunearth_angle函数顾名思义，就是计算星敏和日、地角度的。因为之前的possible_ra/dec有个对应360度旋转的第二维度，所以也要依次遍历计算。
* try-except-else，异常处理语法。运行try后面的语句，如果异常运行except, 没有异常运行else.
* 今日组会：
	* 满足条件的姿态、限制条件具体是什么？这也是我没有看很懂的部分。对地心三轴稳定是什么意思？星敏什么时候有效？在这种状态下（对地心三轴稳定）轨道就可以确定姿态。
	* pobc、数据传输是个什么原理？
	* 目前收到的卫星姿态数据中四元数存在不连续变化情况，正在处理该问题。可能的原因是该时间段星敏没有工作，姿态是通过其他方式确定的。没有星敏数据的时间段应该如何准确得到卫星的状态？
	* 需要从遥测数据中获取星敏的有效数据。并且星敏可能存在“假有效”现象。这都是需要检验的部分。
	* 目前在**尽可能追求更长的开机时间，积累更多数据**，并且利用SAA（辐射异常区）的时间进行数据传输。天格可以随时开关机，没有加高压的准备时间，可以增大开机时间。极区也可以利用。
	* 天格并不是一个圆轨道，因此SAA区的数据可能是要根据轨道和太阳活动调整的。
	* 提出了展示卫星的实时轨道的想法。直接预测计算将来的轨道，然后实时“虚拟”展示。按：展示没必要所有东西都装在一个屏幕上，如果要画曲线可以画在另一个页面上。
	
### 20201130
* 昨天组会上提出的增加开机，利用极地等问题。MIN_HV_ON_TIME是否需要修改。按：已纳入考量。
* select_st_radec_new的选择条件似乎就是星敏和地球、太阳的夹角大于约定值。太阳能板与太阳的夹角小于约定值。原因：被遮挡的时候星敏不工作。所以无法控制指向。
* 想要了解的问题：

  * 关于现在时间段筛选的逻辑。应该是加入了人为调整。答：人为输入的是可以开机的时间段。目前是01:00-20:30。first是判断是否是第一轨，第一轨有些特殊。
  * 关于姿态选择的限制条件。见上面，就是这个。
  * 关于观测计划生成流程。几何以外的有哪些操作。答：如何使用服务器，需要学习linux。检查指令：原理上可以根据轨道、指令txt得到观测计划里绘制的两张图，用来检验计划是否正确。可能会有一些其他问题，具体情况具体分析。
  * 姿态控制时间之外的卫星应该设置成什么状态。答：磁控对日。可以在SAA之外开机。
  * 群里讨论的其他还有哪些需要注意的问题。
* 问题：关于没有解的情况。答：一般不会，可能有bug，目前设置成grid观测，指向虚拟源（正，背对地球）。

## Synthesize:20201130

* 字符串用法：`string.lower()`全部改为小写。

* np.loadtxt()函数：
  -  `fname`要读取的文件、文件名、或生成器。
  -  `dtype`数据类型，默认float。
  -  `comments`注释。如果开头是#，这一行不被读取。
  -  `delimiter`分隔符，默认是空格。
  -  `skiprows`跳过前几行读取，默认是0，必须是int整型。
  -  `usecols`：要读取哪些列，0是第一列。例如，usecols = （1,4,5）将提取第2，第5和第6列。默认读取所有列。
  -  `unpack`如果为`True`，将分列读取。

```python
loadtxt(fname, dtype=, comments='#', delimiter=None, converters=None, skiprows=0, usecols=None, unpack=False, ndmin=0)
```

* 1e-100，这个用法就是10^-100^
* scipy.interpolate.griddata

```python
scipy.interpolate.griddata(points, values, xi, method='linear', fill_value=nan, rescale=False)
```

Parameters :

points: 2-D ndarray of floats with shape (n, D), or length D tuple of 1-D ndarrays with shape (n,).
Data point coordinates.

values: ndarray of float or complex, shape (n,)
Data values.

xi: 2-D ndarray of floats with shape (m, D), or length D tuple of ndarrays broadcastable to the same shape.
Points at which to interpolate data.

method: {‘linear’, ‘nearest’, ‘cubic’}, optional

Returns: ndarray
Array of interpolated values. 

* 所以为什么选用linear而不是cubic? 答：因为没有改原程序……   我这里再次总结一遍：interpolate.griddata这个插值函数的效果，简单来说就是把SAA标准地图上面的辐射值给投射到实际的轨道文件的对应坐标点上。使用了线性插值。可以print看一看。
* 再记一遍：right ascension赤经，declination赤纬。
  所以下面这个算地球的radec是怎么回事？**这里面的天球坐标究竟是怎么定义的？**

```python
earth_ra = orb_ra + np.pi
earth_dec = -orb_dec
```

已解决：相当于在卫星看来地球的位置，可以把卫星和地球认为都在原点，这样的话把原点移到卫星上也不会改变远处天体的RA DEC. by the way, 天球坐标使用的是J2000标准

* 通过find_continous_intervals和Is_too_short两个函数折腾完之后，得到观测目标可行的开始、结束的时间序列的index。
* 程序中是否做了类似把最后计算出来的时间和转向操作等以一种易读的方式输出，来得到一个直观的观测计划，这种？*已提上日程*。
* -y指的是太阳能电池板法线方向。
* st: star tracker星敏。一个类似拍照的设备，用于精确的姿态确定。在很多情况下都不工作。
* install package: pyquaternion-0.9.9
* 四元数计算的结果是一个角度，而非转向。这个角度发送后，卫星通过其他方式（我们不关心）可以调整到这个要求的姿态。这是工作机制。
* HV是什么的缩写？high voltage
* 试运行：已检查至开机时间计算部分，认为三部分时间计算有效：可观测时间（目标在地球遮挡外+可控制）、可姿控时间（有卫星使用权但观测角度被地球遮挡）、无控制时间。得到系列输出i为轨道时间序列orb_time的对应index。
* when blocked: grid_target，使用虚拟目标。如果是以卫星为原点的天球坐标系，虚拟元应该就是背对地球的方向吧？是。
* 探测器轴z、太阳能板法线y（应该是垂直的吧），两轴的方向确定卫星姿态。
* **卫星坐标系**问题：见图片satellite coordinate.png, 星敏自身的指向为(0,0,1), 用安装矩阵乘以它得到卫星坐标系中的指向：(0,sin18,-cos18). 此外，探测器指向为-z，太阳能板法线为-y。
* pl.radec_to_xyz函数就是球坐标系，球面r=1的坐标变换。
* np.cross函数：计算叉乘。
* 四元数的再学习：
  * 基本介绍：四元数都是由实数加上三个虚数单位 i、j、k 组成，而且它们有如下的关系： i^2 = j^2 = k^2 = -1， i^0 = j^0 = k^0 = 1 , 每个四元数都是 1、i、j 和 k 的线性组合，即是四元数一般可表示为a + bi+ cj + dk。对于i、j、k本身的几何意义可以理解为一种旋转，其中i旋转代表XY平面中X轴正向向Y轴正向的旋转，j旋转代表XZ平面中Z轴正向向X轴正向的旋转，k旋转代表YZ平面中Y轴正向向Z轴正向的旋转。
* 四元数旋转的简单应用：对于一个xyz向量(x, y, z), 以这个向量为轴旋转θ角，对应的四元数：cos(θ/2)+xsin(θ/2)·i+ysin(θ/2)·j+zsin(θ/2)·k. 把一个点w=(wx, wy, wz)进行这个旋转操作，就是qw'=q·qw·q^-1^. qw和qw'都是纯四元数，即实部为零，后三项对应的是xyz坐标。
* 好，以下进入possible_st_pointings_new函数。

  * mid的叉乘乘出来是个什么啊？*疑问保留*。答：似乎就是那个叉乘本身的意思，只不过后来用它来对应探测器的指向了。
  * map() 会根据提供的函数对指定序列做映射。`map(function, iterable, ...)`第一个参数 function 以参数序列中的每一个元素调用 function 函数，返回包含每次 function 函数返回值的新列表。返回值是map object类型。
  * Quaternion这个函数生成的旋转四元数就是上面的补充知识说的这一个。但是……为什么我试用下来它应该是以弧度制来接受'angle'的参数的？对没错就是这样，*这里有问题*。
  * 旋转操作.rotate不明。网上查不到文档和出处。内部查找结果，比较可信的是rotate(self, vector)方法。根据观察，它极大可能就是上面四元数知识里面的这种旋转。把这个输入向量按照四元数旋转操作旋转。输出结果为旋转后的向量。
  * 20201128以下。首先，四元数计算操作确认。Quaternion和rotate的用法就是上面写的那样。
  * mid_rot变量想要实现的应该是将mid向量绕目标所在的坐标（天球坐标）与原点所构成的旋转轴，旋转x角度。x从0到360，每10度算一次，一共36个。
  * np.linspace等差数列函数。相当于range(). 三个参数分别是start, end, length. 输出结果类型是np.ndarray.
  * 注意，文件里面的ra-dec都是转换成了弧度的。np的相关计算基本都是基于弧度的，比如sin, cos.
  * quat0里面的是一些四元数，分别对应36个mid_rot向量作为旋转轴，旋转角为（大概）卫星坐标系和天球坐标系的夹角w依次加上一些角度（0到15度，共五个），总计长度为180。
  * `quat = Quaternion(axis=target_pos_xyz, angle=i)`这个地方的angle又用成角度了，*应该转换成弧度*。
  * quat_r，把旋转变换成了quat·quat0的四元数。嗯……不确定这个计算的意义。似乎正式四元数的知识有欠缺。*需要问一下*。答：两个四元数相乘还是一个操作，就是复合，先做一个旋转，再做另一个旋转的意思。几何原理不明中。
  * 最后的输出就是detector&solar panet指向的一个序列。
  * 20201129注：角度问题已经修改。
* 关于时间问题：北京时间、utc、unix的区分：utc( Universal Time Coordinated ), 协调世界时。一种统一计时法。据unix时间戳词条介绍，Unix时间戳（英文为Unix epoch, Unix time, POSIX time 或 Unix timestamp）是从1970年1月1日（UTC/GMT的午夜）开始所经过的秒数，不考虑闰秒。北京时间与utc应该是相差八个时区。
* 直接从轨道文件中读取的orb_time_bj的格式是2020-11-18T23:59:50.000这种类型。后面的orb_time操作将其减去8个小时，并且转换成unix秒数格式，成为utc的标准形式。
* 接昨天，计算出detector&solar panet指向后，func.calc_st_radec计算星敏的指向，有一个18度夹角，比较简单。
* calculate_sunearth_angle函数顾名思义，就是计算星敏和日、地角度的。因为之前的possible_ra/dec有个对应360度旋转的第二维度，所以也要依次遍历计算。
* try-except-else，异常处理语法。运行try后面的语句，如果异常运行except, 没有异常运行else.
* 20201129组会：
  * 满足条件的姿态、限制条件具体是什么？这也是我没有看很懂的部分。对地心三轴稳定是什么意思？星敏什么时候有效？在这种状态下（对地心三轴稳定）轨道就可以确定姿态。
  * pobc、数据传输是个什么原理？
  * 目前收到的卫星姿态数据中四元数存在不连续变化情况，正在处理该问题。可能的原因是该时间段星敏没有工作，姿态是通过其他方式确定的。没有星敏数据的时间段应该如何准确得到卫星的状态？
  * 需要从遥测数据中获取星敏的有效数据。并且星敏可能存在“假有效”现象。这都是需要检验的部分。
  * 目前在**尽可能追求更长的开机时间，积累更多数据**，并且利用SAA（辐射异常区）的时间进行数据传输。天格可以随时开关机，没有加高压的准备时间，可以增大开机时间。极区也可以利用。
  * 天格并不是一个圆轨道，因此SAA区的数据可能是要根据轨道和太阳活动调整的。
  * 提出了展示卫星的实时轨道的想法。直接预测计算将来的轨道，然后实时“虚拟”展示。按：展示没必要所有东西都装在一个屏幕上，如果要画曲线可以画在另一个页面上。
* 昨天组会上提出的增加开机，利用极地等问题。MIN_HV_ON_TIME是否需要修改。按：已纳入考量。
* select_st_radec_new的选择条件似乎就是星敏和地球、太阳的夹角大于约定值。太阳能板与太阳的夹角小于约定值。原因：被遮挡的时候星敏不工作。所以无法控制指向。
* 想要了解的问题：

  * 关于现在时间段筛选的逻辑。应该是加入了人为调整。答：人为输入的是可以开机的时间段。目前是01:00-20:30。first是判断是否是第一轨，第一轨有些特殊。
  * 关于姿态选择的限制条件。见上面，就是这个。
  * 关于观测计划生成流程。几何以外的有哪些操作。答：如何使用服务器，需要学习linux。检查指令：原理上可以根据轨道、指令txt得到观测计划里绘制的两张图，用来检验计划是否正确。可能会有一些其他问题，具体情况具体分析。
  * 姿态控制时间之外的卫星应该设置成什么状态。答：磁控对日。可以在SAA之外开机。
  * 群里讨论的其他还有哪些需要注意的问题。
* 问题：关于没有解的情况。答：一般不会，可能有bug，目前设置成grid观测，指向虚拟源（正，背对地球）。