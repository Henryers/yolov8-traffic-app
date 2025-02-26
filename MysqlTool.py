import pymysql
class MysqlTool:
    def __init__(self):
        """mysql 连接初始化"""
        self.host = '127.0.0.1'  # 数据库主机名
        self.port = 3306  # 数据库端口号，默认为3306
        self.user = 'root'  # 数据库用户名
        self.password = '20040111'  # 数据库密码
        self.db = 'pyqt_yolov8'  # 数据库名称
        self.charset = 'utf8'  # 字符编码
        self.mysql_conn = None
    def __enter__(self):
        """打开数据库连接"""
        self.mysql_conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            passwd=self.password,
            db=self.db,
            charset=self.charset
        )
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        """关闭数据库连接"""
        if self.mysql_conn:
            self.mysql_conn.close()
            self.mysql_conn = None
    def execute(self, sql: str, args: tuple = None, commit: bool = False) -> any:
        # 外部传参为：sql语句、带参数的元组、是否提交(要插入就提交，查询就不用)
        """执行 SQL 语句"""
        try:
            # 创建游标并起别名
            with self.mysql_conn.cursor() as cursor:
                cursor.execute(sql, args)
                if commit:
                    self.mysql_conn.commit()
                    print(f"执行 SQL 语句：{sql}，参数：{args}，数据提交成功")
                else:
                    # 查询所有行数据
                    result = cursor.fetchall()
                    print(f"执行 SQL 语句：{sql}，参数：{args}，查询到的数据为：{result}")
                    return result
        except Exception as e:
            print(f"执行 SQL 语句出错：{e}")
            self.mysql_conn.rollback()
            raise e
